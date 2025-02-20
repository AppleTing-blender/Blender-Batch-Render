import customtkinter as ctk
from CTkListbox import CTkListbox  # CTkListbox 임포트
from tkinter import filedialog, messagebox
import subprocess
import os
import sys
import threading

class BlenderRenderer:
    def __init__(self, root):
        self.root = root
        self.root.title("순차적 렌더러")
        
        # 창의 크기를 조절하지 못하도록 설정
        self.root.resizable(False, False)
        
        # CustomTkinter 테마 설정
        ctk.set_appearance_mode("system")  # "light" 또는 "dark"로 설정 가능
        ctk.set_default_color_theme("blue")  # 테마 색상 설정

        self.input_files = []
        self.output_directory = ctk.StringVar()
        self.start_frame = ctk.StringVar(value='0')  # 시작 프레임 기본값을 0으로 설정

        # 추가된 변수
        self.frame_mode = ctk.StringVar(value="default")
        self.blender_path = ctk.StringVar(value=self.find_blender_path())  # 블렌더 경로 기본값 설정


        self.temp_script_path = r"C:\temp\temp_script.py"
        self.create_temp_script()
        self.create_widgets()

    def create_temp_script(self):
        temp_script_content = """
import bpy
import os
import sys

blend_file = sys.argv[sys.argv.index('--') + 1]
output_directory = sys.argv[sys.argv.index('--') + 2]
try:
    start_frame = int(sys.argv[sys.argv.index('--') + 3])
except (IndexError, ValueError):
    start_frame = bpy.context.scene.frame_start  # 기본 시작 프레임 설정

blend_file = os.path.normpath(blend_file)
output_directory = os.path.normpath(output_directory)

bpy.ops.wm.open_mainfile(filepath=blend_file)

file_output_folder = os.path.join(output_directory, os.path.splitext(os.path.basename(blend_file))[0])
if not os.path.exists(file_output_folder):
    os.makedirs(file_output_folder)

end_frame = bpy.context.scene.frame_end

for frame in range(start_frame, end_frame + 1):
    bpy.context.scene.frame_set(frame)
    output_filepath = os.path.join(file_output_folder, f"{os.path.splitext(os.path.basename(blend_file))[0]}_{frame:04d}.png")
    bpy.context.scene.render.filepath = output_filepath
    bpy.ops.render.render(write_still=True)
"""
        os.makedirs(os.path.dirname(self.temp_script_path), exist_ok=True)
        with open(self.temp_script_path, 'w') as f:
            f.write(temp_script_content)
        
    def create_widgets(self):
    
        # 큰 프레임 설정
        main_frame = ctk.CTkFrame(self.root, corner_radius=10)
        main_frame.pack(pady=10, padx=10, fill='both', expand=True)

        # 블렌더 경로 설정 부분
        blender_path_container_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        blender_path_container_frame.pack(pady=10, padx=20, fill='both')

        blender_path_label_frame = ctk.CTkFrame(blender_path_container_frame, fg_color="#191919", corner_radius=10)
        blender_path_label_frame.pack(fill='x', anchor='nw')

        ctk.CTkLabel(blender_path_label_frame, text="블렌더 실행 파일", text_color="white").pack(side='left', padx=10, pady=5)

        blender_path_entry_frame = ctk.CTkFrame(blender_path_container_frame, fg_color="transparent", corner_radius=10)
        blender_path_entry_frame.pack(fill='x', anchor='nw')

        ctk.CTkEntry(blender_path_entry_frame, textvariable=self.blender_path, width=400).pack(side='left', padx=10, pady=20, fill='x')
        ctk.CTkButton(blender_path_entry_frame, text=" . . . ", command=self.select_blender_path, width=80, height=30).pack(side='left', padx=10, pady=5)
            
        # 블렌더 파일 선택 부분
        container_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        container_frame.pack(pady=2, padx=20, anchor='nw', fill='both')

        label_frame = ctk.CTkFrame(container_frame, fg_color="#191919", corner_radius=10)
        label_frame.pack(fill='x', anchor='nw')

        ctk.CTkLabel(label_frame, text="렌더 파일 선택", text_color="white").pack(side='left', padx=10, pady=5)

        listbox_and_buttons_frame = ctk.CTkFrame(container_frame, corner_radius=10)
        listbox_and_buttons_frame.pack(fill='x', anchor='nw')

        # 리스트박스에 제목 추가
        ctk.CTkLabel(listbox_and_buttons_frame, text="순번").pack(anchor='w', padx=10, pady=5)

        self.file_listbox = CTkListbox(listbox_and_buttons_frame, width=375, height=150)
        self.file_listbox.pack(side='left', padx=10, pady=5)

        reorder_buttons_frame = ctk.CTkFrame(listbox_and_buttons_frame, fg_color="transparent", corner_radius=10)
        reorder_buttons_frame.pack(side='left', padx=10, pady=5)

        ctk.CTkButton(reorder_buttons_frame, text="△", command=self.move_up, width=30, height=30).pack(pady=2)
        ctk.CTkButton(reorder_buttons_frame, text="▽", command=self.move_down, width=30, height=30).pack(pady=2)

        # 파일 추가/제거 버튼
        button_frame = ctk.CTkFrame(container_frame, fg_color="transparent", corner_radius=10)
        button_frame.pack(pady=5, fill='x')

        ctk.CTkButton(button_frame, text="+", command=self.select_blend_files, width=30, height=30).pack(side='left', padx=10, pady=5)
        ctk.CTkButton(button_frame, text="-", command=self.delete_selected_files, width=30, height=30).pack(side='left', padx=1, pady=5)

        # 출력 경로 설정 부분
        output_container_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        output_container_frame.pack(pady=1, padx=20, fill='both')

        output_label_frame = ctk.CTkFrame(output_container_frame, fg_color="#191919", corner_radius=10)
        output_label_frame.pack(fill='x', anchor='nw')

        ctk.CTkLabel(output_label_frame, text="출력 경로", text_color="white").pack(side='left', padx=10, pady=5)

        output_entry_frame = ctk.CTkFrame(output_container_frame, fg_color="transparent", corner_radius=10)
        output_entry_frame.pack(fill='x', anchor='nw')

        ctk.CTkEntry(output_entry_frame, textvariable=self.output_directory, width=400).pack(side='left', padx=10, pady=20, fill='x')
        ctk.CTkButton(output_entry_frame, text=" . . . ", command=self.select_output_directory, width=80, height=30).pack(side='left', padx=10, pady=5)

        # 시작 프레임 설정 부분
        frame_container_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color="transparent")
        frame_container_frame.pack(pady=5, padx=20, anchor='nw')

        frame_label_frame = ctk.CTkFrame(frame_container_frame, fg_color="#191919", corner_radius=10)
        frame_label_frame.pack(fill='x', anchor='nw')

        ctk.CTkLabel(frame_label_frame, text="시작 프레임", text_color="white").pack(side='left', padx=10, pady=5)

        frame_entry_frame = ctk.CTkFrame(frame_container_frame, fg_color="transparent", corner_radius=10)
        frame_entry_frame.pack(fill='x', anchor='nw')

        frame_mode_frame = ctk.CTkFrame(frame_entry_frame, fg_color="transparent", corner_radius=10)
        frame_mode_frame.pack(fill='x', pady=5)

        ctk.CTkRadioButton(frame_mode_frame, text="기본 설정 프레임", variable=self.frame_mode, value="default", command=self.toggle_entry_state).pack(side='left', padx=10, pady=5)
        
        custom_frame = ctk.CTkFrame(frame_mode_frame, fg_color="transparent", corner_radius=10)
        custom_frame.pack(side='left', padx=10, pady=5)

        ctk.CTkRadioButton(custom_frame, text="직접 설정", variable=self.frame_mode, value="custom", command=self.toggle_entry_state).pack(side='left')
        self.start_frame_entry = ctk.CTkEntry(custom_frame, textvariable=self.start_frame, width=100)
        self.start_frame_entry.pack(side='left', padx=10)

        self.toggle_entry_state()  # 초기 상태 설정

        # 실행 버튼
        ctk.CTkButton(main_frame, text="실행하기", command=self.run_rendering, width=80, height=30).pack(pady=20)

    def toggle_entry_state(self):
        if self.frame_mode.get() == "custom":
            self.start_frame_entry.configure(state='normal')
        else:
            self.start_frame_entry.configure(state='disabled')

    def select_blender_path(self):
        file_path = filedialog.askopenfilename(title="Select Blender Executable", filetypes=[("Blender Executable", "blender.exe")])
        if file_path:
            self.blender_path.set(file_path)

    def select_blend_files(self):
        file_paths = filedialog.askopenfilenames(title="Select Blender Files", filetypes=[("Blender Files", "*.blend")])
        if file_paths:
            for file_path in file_paths:
                if file_path not in self.input_files:
                    display_name = os.path.basename(file_path)  # 파일 이름만 표시
                    self.input_files.append(file_path)
                    self.file_listbox.insert(ctk.END, display_name)

    def delete_selected_files(self):
        selected_indices = self.file_listbox.curselection()
        selected_indices = list(selected_indices) if isinstance(selected_indices, tuple) else [selected_indices]
        for index in reversed(selected_indices):
            if index is not None:
                self.file_listbox.delete(int(index))
                del self.input_files[index]

    def move_up(self):
        try:
            selected_indices = self.file_listbox.curselection()
            selected_indices = list(selected_indices) if isinstance(selected_indices, tuple) else [selected_indices]
            for index in selected_indices:
                if index is not None and index > 0:
                    # 리스트박스 항목 이동
                    self.file_listbox.move_up(index)
                    # input_files 항목 이동
                    self.input_files.insert(index - 1, self.input_files.pop(index))
        except Exception as e:
            print(f"An error occurred: {e}")

    def move_down(self):
        try:
            selected_indices = self.file_listbox.curselection()
            selected_indices = list(selected_indices) if isinstance(selected_indices, tuple) else [selected_indices]
            for index in reversed(selected_indices):
                if index is not None and index < len(self.file_listbox.buttons) - 1:
                    # 리스트박스 항목 이동
                    self.file_listbox.move_down(index)
                    # input_files 항목 이동
                    self.input_files.insert(index + 1, self.input_files.pop(index))
        except Exception as e:
            print(f"An error occurred: {e}")

    def select_output_directory(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_directory.set(directory)

    def find_blender_path(self):
        base_path = r"C:\Program Files\Blender Foundation"
        versions = [d for d in os.listdir(base_path) if d.startswith("Blender")]
        if not versions:
            return None
        latest_version = sorted(versions, reverse=True)[0]
        return os.path.join(base_path, latest_version, "blender.exe")
    
    def run_rendering(self):
        output_directory = self.output_directory.get()
        start_frame = self.start_frame.get()

        if not self.input_files or not output_directory or not start_frame:
            messagebox.showerror("오류", "블렌더 파일, 출력 경로 및 시작 프레임을 모두 선택해야 합니다.")
            return

        try:
            start_frame = int(start_frame)
        except ValueError:
            messagebox.showerror("오류", "시작 프레임은 숫자여야 합니다.")
            return

        # 블렌더 실행 파일 경로 설정
        blender_path = self.blender_path.get()
        if not blender_path or not os.path.isfile(blender_path):
            messagebox.showerror("오류", "블렌더 실행 파일을 찾을 수 없습니다.")
            
        # 실제 파일 경로 가져오기
        selected_files = self.input_files

        self.render_files_sequentially(blender_path, selected_files, output_directory, start_frame)

    def render_files_sequentially(self, blender_path, selected_files, output_directory, start_frame):
        for i, blend_file in enumerate(selected_files):
            blend_file = os.path.normpath(blend_file)  # 경로 문자열 형식 정규화
            self.run_blender_subprocess(blender_path, blend_file, output_directory, start_frame if i == 0 else None)
            # 마지막 블렌더 파일이 렌더링된 후 임시 스크립트 삭제
            if i == len(selected_files) - 1:
                if os.path.exists(self.temp_script_path):
                    os.remove(self.temp_script_path)

    def run_blender_subprocess(self, blender_path, blend_file, output_directory, start_frame):
        script_args = [blender_path, "-b", blend_file, "-P", self.temp_script_path, "--", blend_file, output_directory]
        if start_frame is not None:
            script_args.append(str(start_frame))

        process = subprocess.Popen(script_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')

        for line in process.stdout:
            print(line, end="")
        for line in process.stderr:
            print(line, end="")

        process.wait()  # 현재 프로세스가 종료될 때까지 대기

if __name__ == "__main__":
    root = ctk.CTk()
    app = BlenderRenderer(root)
    root.mainloop()