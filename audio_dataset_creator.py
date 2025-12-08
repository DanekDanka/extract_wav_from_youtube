import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
import subprocess
from pathlib import Path
import random

class AudioDatasetCreator:
    def __init__(self, root):
        self.root = root
        self.root.title("Создатель датасета аудиозаписей")
        self.root.geometry("900x700")

        # Переменные для хранения данных
        self.dataset_path = tk.StringVar()
        self.common_id = tk.StringVar()
        self.entries = []

        # Устанавливаем путь по умолчанию
        self.dataset_path.set("/home/danya/datasets/speech_vetification/")

        self.create_widgets()

    def create_widgets(self):
        # Основной фрейм с скроллом
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Создаем Canvas и Scrollbar
        self.canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Упаковываем Canvas и Scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Привязываем колесо мыши к скроллу
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)

        # Поле для выбора пути сохранения
        ttk.Label(self.scrollable_frame, text="Путь для сохранения датасета:").pack(pady=5, anchor="w")
        path_frame = ttk.Frame(self.scrollable_frame)
        path_frame.pack(pady=5, fill=tk.X, padx=10)

        ttk.Entry(path_frame, textvariable=self.dataset_path, width=60).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(path_frame, text="Обзор", command=self.browse_path).pack(side=tk.LEFT)

        # Общее поле ID
        ttk.Label(self.scrollable_frame, text="Общий ID для всех записей:").pack(pady=5, anchor="w")
        id_frame = ttk.Frame(self.scrollable_frame)
        id_frame.pack(pady=5, fill=tk.X, padx=10)

        ttk.Entry(id_frame, textvariable=self.common_id, width=20).pack(side=tk.LEFT)

        # Фрейм для кнопок управления
        buttons_frame = ttk.Frame(self.scrollable_frame)
        buttons_frame.pack(pady=10, fill=tk.X)

        # Кнопка добавления новой записи
        ttk.Button(buttons_frame, text="+ Добавить запись", command=self.add_entry).pack(side=tk.LEFT, padx=5)

        # Кнопка очистки
        ttk.Button(buttons_frame, text="Очистить все", command=self.clear_all).pack(side=tk.LEFT, padx=5)

        # Фрейм для записей
        self.entries_frame = ttk.Frame(self.scrollable_frame)
        self.entries_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Кнопка обработки
        ttk.Button(self.scrollable_frame, text="Скачать и обработать аудио", command=self.process_audio).pack(pady=10)

        # Добавляем первую запись
        self.add_entry()

    def _on_mousewheel(self, event):
        """Обработка скролла колесом мыши"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.dataset_path.set(path)

    def clear_all(self):
        """Очищает все поля кроме пути сохранения"""
        # Очищаем общий ID
        self.common_id.set("")

        # Удаляем все записи
        for entry in self.entries:
            entry['frame'].destroy()

        self.entries.clear()

        # Добавляем одну пустую запись
        self.add_entry()

        messagebox.showinfo("Очистка", "Все поля очищены!")

    def add_entry(self):
        entry_frame = ttk.LabelFrame(self.entries_frame, text=f"Запись {len(self.entries) + 1}")
        entry_frame.pack(fill=tk.X, pady=5)

        # Год записи
        ttk.Label(entry_frame, text="Год аудиозаписи:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        year_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable=year_var, width=10).grid(row=0, column=1, padx=5, pady=2)

        # Ссылка на YouTube
        ttk.Label(entry_frame, text="Ссылка на YouTube:").grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        url_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable=url_var, width=50).grid(row=0, column=3, columnspan=4, padx=5, pady=2, sticky=tk.W+tk.E)

        # Фрейм для таймкодов
        times_frame = ttk.LabelFrame(entry_frame, text="Таймкоды (Start-End)")
        times_frame.grid(row=1, column=0, columnspan=6, padx=5, pady=5, sticky=tk.W+tk.E)

        # Список таймкодов для этой записи
        time_entries = []

        def add_time_entry():
            time_entry_frame = ttk.Frame(times_frame)
            time_entry_frame.pack(fill=tk.X, pady=2)

            ttk.Label(time_entry_frame, text="Start:").pack(side=tk.LEFT, padx=(5, 2))
            start_var = tk.StringVar()
            ttk.Entry(time_entry_frame, textvariable=start_var, width=10).pack(side=tk.LEFT, padx=2)

            ttk.Label(time_entry_frame, text="End:").pack(side=tk.LEFT, padx=(10, 2))
            end_var = tk.StringVar()
            ttk.Entry(time_entry_frame, textvariable=end_var, width=10).pack(side=tk.LEFT, padx=2)

            remove_btn = ttk.Button(time_entry_frame, text="✕", width=3,
                                  command=lambda f=time_entry_frame, s=start_var, e=end_var: remove_time_entry(f, s, e))
            remove_btn.pack(side=tk.LEFT, padx=5)

            time_entries.append({'start': start_var, 'end': end_var, 'frame': time_entry_frame})

        def remove_time_entry(frame, start_var, end_var):
            for i, te in enumerate(time_entries):
                if te['frame'] == frame:
                    time_entries.pop(i)
                    frame.destroy()
                    break

        # Кнопка добавления таймкода
        add_time_btn = ttk.Button(times_frame, text="+ Добавить таймкод", command=add_time_entry)
        add_time_btn.pack(pady=5)

        # Добавляем первый таймкод по умолчанию
        add_time_entry()

        # Кнопка удаления всей записи
        remove_btn = ttk.Button(entry_frame, text="Удалить запись",
                               command=lambda f=entry_frame: self.remove_entry(f))
        remove_btn.grid(row=2, column=5, padx=5, pady=2)

        entry_data = {
            'frame': entry_frame,
            'year': year_var,
            'url': url_var,
            'time_entries': time_entries,
            'add_time_func': add_time_entry
        }

        self.entries.append(entry_data)

        # Обновляем скролл регион после добавления новой записи
        self.root.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def remove_entry(self, frame):
        for i, entry in enumerate(self.entries):
            if entry['frame'] == frame:
                self.entries.pop(i)
                frame.destroy()
                self.renumber_entries()
                break

        # Обновляем скролл регион после удаления записи
        self.root.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def renumber_entries(self):
        for i, entry in enumerate(self.entries):
            entry['frame'].configure(text=f"Запись {i + 1}")

    def download_youtube_audio(self, url, output_path, max_retries=5):
        """Скачивает аудио с YouTube с обходом антибот-защиты и повторными попытками"""
        # Случайный user-agent из списка популярных
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            # Настройки для обхода антибот-защиты
            'http_headers': {
                'User-Agent': random.choice(user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip,deflate',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'Connection': 'keep-alive',
            },
            'extract_flat': False,
            'ignoreerrors': False,  # Отключаем, чтобы получать исключения и обрабатывать их
            'no_warnings': False,
            'quiet': False,
            'verbose': True,
            # Настройки повторных попыток
            'retries': 10,
            'fragment_retries': 10,
            'file_access_retries': 5,
            'sleep_interval': 3,
            'max_sleep_interval': 10,
            'sleep_interval_requests': 1,
            # Дополнительные настройки
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['configs', 'webpage']
                }
            },
            'compat_opts': ['no-youtube-unavailable-video'],
        }

        for attempt in range(max_retries):
            try:
                # Меняем user-agent при каждой попытке
                ydl_opts['http_headers']['User-Agent'] = random.choice(user_agents)
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                return True
            except Exception as e:
                error_str = str(e).lower()
                # Проверяем, является ли ошибка временной (503, 429 и т.д.)
                if '503' in error_str or '429' in error_str or 'service unavailable' in error_str or 'too many requests' in error_str:
                    wait_time = (attempt + 1) * 10  # 10, 20, 30, 40, 50 секунд
                    print(f"Ошибка сервера (попытка {attempt + 1}/{max_retries}): {e}")
                    print(f"Ожидание {wait_time} секунд перед повторной попыткой...")
                    time.sleep(wait_time)
                else:
                    print(f"Ошибка при скачивании (попытка {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5
                        print(f"Ожидание {wait_time} секунд перед повторной попыткой...")
                        time.sleep(wait_time)
        
        # Если все попытки не удались, пробуем альтернативный подход
        print("Основной метод не сработал, пробуем альтернативный...")
        return self.download_youtube_audio_alternative(url, output_path)

    def download_youtube_audio_alternative(self, url, output_path, max_retries=3):
        """Альтернативный метод скачивания с другими настройками"""
        for attempt in range(max_retries):
            try:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': output_path,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'wav',
                        'preferredquality': '192',
                    }],
                    'extract_flat': False,
                    'ignoreerrors': False,
                    'no_warnings': False,
                    'quiet': False,
                    'retries': 10,
                    'fragment_retries': 10,
                    'sleep_interval': 5,
                    'max_sleep_interval': 15,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['ios', 'android'],
                            'player_skip': ['configs', 'webpage', 'js']
                        }
                    },
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                return True
            except Exception as e:
                print(f"Ошибка при альтернативном скачивании (попытка {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 15
                    print(f"Ожидание {wait_time} секунд перед повторной попыткой...")
                    time.sleep(wait_time)
        
        return False

    def extract_audio_segment(self, input_file, output_file, start_time, end_time):
        """Извлекает сегмент аудио с помощью ffmpeg"""
        try:
            cmd = [
                'ffmpeg',
                '-loglevel', 'panic',
                '-i', input_file,
                '-ss', start_time,
                '-t', str(self.time_to_seconds(end_time) - self.time_to_seconds(start_time)),
                '-ac', '1',
                '-ar', '16000',
                '-sample_fmt', 's16',
                '-y',
                output_file
            ]
            subprocess.run(cmd, check=True)
            return True
        except Exception as e:
            print(f"Ошибка при обработке аудио: {e}")
            return False

    def concatenate_audio_files(self, input_files, output_file):
        """Склеивает несколько аудиофайлов в один"""
        try:
            # Создаем временный файл со списком файлов для склейки
            list_file = Path(output_file).parent / "concat_list.txt"
            with open(list_file, 'w') as f:
                for input_file in input_files:
                    f.write(f"file '{input_file}'\n")

            cmd = [
                'ffmpeg',
                '-loglevel', 'panic',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(list_file),
                '-ac', '1',
                '-ar', '16000',
                '-sample_fmt', 's16',
                '-y',
                output_file
            ]
            subprocess.run(cmd, check=True)

            # Удаляем временный файл
            list_file.unlink()
            return True
        except Exception as e:
            print(f"Ошибка при склейке аудио: {e}")
            return False

    def time_to_seconds(self, time_str):
        """Конвертирует время в формате HH:MM:SS в секунды"""
        h, m, s = time_str.split(':')
        return int(h) * 3600 + int(m) * 60 + int(s)

    def print_url_list(self):
        """Выводит список URL и годов в консоль"""
        print("\n" + "="*50)
        print("СПИСОК ОБРАБОТАННЫХ АУДИОЗАПИСЕЙ:")
        print("="*50)

        for i, entry in enumerate(self.entries, 1):
            url = entry['url'].get().strip()
            year = entry['year'].get().strip()
            print(f"{i}. {url} ({year})")

        print("="*50)

    def process_audio(self):
        if not self.dataset_path.get():
            messagebox.showerror("Ошибка", "Укажите путь для сохранения датасета")
            return

        if not self.common_id.get().strip():
            messagebox.showerror("Ошибка", "Укажите общий ID")
            return

        # Проверяем все поля и таймкоды
        for i, entry in enumerate(self.entries, 1):
            year = entry['year'].get().strip()
            url = entry['url'].get().strip()
            time_entries = entry['time_entries']

            if not year or not url:
                messagebox.showerror("Ошибка", f"Все поля должны быть заполнены в записи {i}")
                return

            if len(time_entries) == 0:
                messagebox.showerror("Ошибка", f"Добавьте хотя бы один таймкод в записи {i}")
                return

            for j, time_entry in enumerate(time_entries, 1):
                start = time_entry['start'].get().strip()
                end = time_entry['end'].get().strip()
                if not start or not end:
                    messagebox.showerror("Ошибка", f"Все таймкоды должны быть заполнены в записи {i}, таймкод {j}")
                    return

        # Создаем временную папку для скачанных файлов
        temp_dir = Path(self.dataset_path.get()) / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        success_count = 0
        total_count = len(self.entries)
        id_val = self.common_id.get().strip()

        for entry in self.entries:
            year = entry['year'].get().strip()
            url = entry['url'].get().strip()
            time_entries = entry['time_entries']

            # Создаем структуру папок
            speaker_dir = Path(self.dataset_path.get()) / f"id{id_val.zfill(5)}"
            year_dir = speaker_dir / year
            year_dir.mkdir(parents=True, exist_ok=True)

            output_file = year_dir / f"{id_val.zfill(5)}.wav"
            temp_file = temp_dir / f"temp_{id_val}_{year}.wav"

            # Скачиваем аудио
            print(f"Скачивание аудио для ID {id_val}, год {year}...")
            if not self.download_youtube_audio(url, str(temp_file.with_suffix(''))):
                messagebox.showerror("Ошибка", f"Не удалось скачать аудио для ID {id_val}, год {year}")
                continue

            # Проверяем, что файл был скачан
            downloaded_file = temp_file.with_suffix('.wav')
            if not downloaded_file.exists():
                print(f"Файл не был скачан: {downloaded_file}")
                continue

            # Обрабатываем каждый таймкод
            segment_files = []
            for j, time_entry in enumerate(time_entries):
                start_time = time_entry['start'].get().strip()
                end_time = time_entry['end'].get().strip()

                segment_file = temp_dir / f"segment_{id_val}_{year}_{j}.wav"

                print(f"Извлечение сегмента {j+1} для ID {id_val}, год {year}...")
                if self.extract_audio_segment(str(downloaded_file), str(segment_file), start_time, end_time):
                    segment_files.append(str(segment_file))
                    print(f"Успешно извлечен сегмент: {segment_file}")

            # Склеиваем сегменты если их больше одного
            if len(segment_files) == 1:
                # Если сегмент один, просто копируем его
                Path(segment_files[0]).rename(output_file)
                success_count += 1
                print(f"Успешно обработано: {output_file}")
            elif len(segment_files) > 1:
                # Если несколько сегментов, склеиваем их
                if self.concatenate_audio_files(segment_files, str(output_file)):
                    success_count += 1
                    print(f"Успешно склеено и обработано: {output_file}")

                # Удаляем временные сегменты
                for seg_file in segment_files:
                    try:
                        Path(seg_file).unlink()
                    except:
                        pass

            # Удаляем временный файл
            try:
                if downloaded_file.exists():
                    downloaded_file.unlink()
            except:
                pass

        # Удаляем временную папку
        try:
            for file in temp_dir.glob("*"):
                file.unlink()
            temp_dir.rmdir()
        except:
            pass

        # Выводим список URL в консоль
        self.print_url_list()

        messagebox.showinfo("Готово",
                          f"Обработка завершена!\n"
                          f"Успешно обработано: {success_count}/{total_count} записей\n"
                          f"Датасет сохранен в: {self.dataset_path.get()}")

def main():
    root = tk.Tk()
    app = AudioDatasetCreator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
