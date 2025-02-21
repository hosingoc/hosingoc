import json
import os
import sys
import threading
import time
import webbrowser
from sys import exit
import about
import fitz  # PyMuPDF
import PyPDF2
from PIL import Image, ImageDraw, ImageFont, ImageTk
from docx import Document
import tkinter as tk
from tkinter import Button, Menu, PhotoImage, Tk, filedialog, messagebox, simpledialog, ttk
from ImageEditor import ImageEditorWindow, edit_image

from settings import load_settings
from ui_settings import open_settings_and_switch_tab
from update import check_for_updates, download_update_with_progress, open_software_update_tab
from about import translate
from about import show_about, refresh_ui

from translate import translate, change_language



# Đặt lại thư mục làm việc (working directory) về thư mục chứa script Python
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Kiểm tra lại thư mục làm việc sau khi thay đổi
print("Current working directory:", os.getcwd())




# Biến lưu trữ ngôn ngữ hiện tại
current_language = "vi"

# Hàm tải bản dịch từ tệp JSON
def load_translations(language_code):
    """Load translations from JSON file"""
    try:
        translation_path = os.path.join(
            os.path.dirname(__file__), 
            "translations", 
            f"{language_code}.json"
        )
        print(f"Loading translations from: {translation_path}")
        
        with open(translation_path, "r", encoding="utf-8") as f:
            translations = json.load(f)
            print(f"Successfully loaded {len(translations)} translations for {language_code}")
            return translations
            
    except FileNotFoundError:
        print(f"Translation file not found: {language_code}.json") 
        return {}
    except json.JSONDecodeError:
        print(f"Invalid JSON in translation file: {language_code}.json")
        return {}
    except Exception as e:
        print(f"Error loading translations: {e}")
        return {}

# Lấy bản dịch cho một key
def translate(key):
    """Get translation for key in current language"""
    global translations
    if not translations:
        translations = load_translations(current_language)
    return translations.get(key, key)

# Cập nhật ngôn ngữ ứng dụng
def change_language(lang_code):
    """Change current language and update UI"""
    global current_language, translations
    
    # Cập nhật ngôn ngữ
    current_language = lang_code
    
    # Load translations mới
    translations = load_translations(lang_code)
    
    # Gọi hàm on_language_change để cập nhật UI
    on_language_change(lang_code)
    
    return translations

# Lưu bản dịch vào biến global translations
translations = load_translations(current_language)

# Lưu trạng thái của các trường nhập liệu
history = []

# Hàm lưu lại trạng thái của các trường nhập liệu
def save_state():
    state = {
        "input_pdf": input_pdf_entry.get(),
        "output_folder": output_folder_entry.get(),
        "input_pdfs": input_pdfs_entry.get(),
        "output_pdf": output_pdf_entry.get()
    }
    history.append(state)

# Hàm Undo: khôi phục lại trạng thái trước đó
def undo():
    if history:
        previous_state = history.pop()  # Lấy trạng thái trước đó
        input_pdf_entry.delete(0, tk.END)
        input_pdf_entry.insert(0, previous_state.get("input_pdf", ""))
        output_folder_entry.delete(0, tk.END)
        output_folder_entry.insert(0, previous_state.get("output_folder", ""))
        input_pdfs_entry.delete(0, tk.END)
        input_pdfs_entry.insert(0, previous_state.get("input_pdfs", ""))
        output_pdf_entry.delete(0, tk.END)
        output_pdf_entry.insert(0, previous_state.get("output_pdf", ""))

# Hàm Clear All: xóa tất cả thông tin nhập vào
def clear_all():
    input_pdf_entry.delete(0, tk.END)
    output_folder_entry.delete(0, tk.END)
    input_pdfs_entry.delete(0, tk.END)
    output_pdf_entry.delete(0, tk.END)
        
    
def create_main_tab():
    # Tạo tab chính
    main_tab = ttk.Frame(notebook)
    notebook.add(main_tab, text="Main")

    # Thêm nút vào tab chính sử dụng grid
    open_images_button = tk.Button(main_tab, text="Mở ảnh để chỉnh sửa")
    open_images_button.grid(row=0, column=0, pady=20, padx=20)


   
def open_email(event):
    webbrowser.open("mailto:contact@ngoc.info")

# Biến toàn cục để lưu `about_tab`
about_tab = None

def show_about_page(notebook):
    """Hiển thị hoặc cập nhật tab About nếu chưa tồn tại."""
    for tab in notebook.tabs():
        if notebook.tab(tab, "text") == translate("about"):
            notebook.select(tab)
            refresh_ui(notebook, tab)
            return

    about_tab = show_about(notebook)  # Tạo tab mới
    refresh_ui(notebook, about_tab)



def open_file():
    file_path = filedialog.askopenfilename(title="Chọn một ảnh", filetypes=(("Image files", "*.png;*.jpg;*.jpeg;*.bmp"), ("All files", "*.*")))
    if file_path:
        # Gọi hàm edit_image từ ImageEditor.py để xử lý ảnh
        edit_image(file_path)  # Truyền đường dẫn file ảnh vào hàm edit_image   

   
# Hàm thay đổi màu sắc và con trỏ chuột chung cho tất cả widgets
def on_enter(event, widget):
    widget.config(fg="blue")  # Thay đổi màu chữ khi rê chuột vào
    widget.config(cursor="hand2")  # Thay đổi con trỏ thành ngón tay

def on_leave(event, widget):
    widget.config(fg="black")  # Thay đổi màu chữ khi rê chuột ra ngoài
    widget.config(cursor="arrow")  # Khôi phục con trỏ chuột mặc định

def on_click(event, widget):
    widget.config(fg="red")  # Thay đổi màu chữ khi click

# Hàm đăng ký sự kiện cho nhiều widget
def add_interaction(widget):
    widget.bind("<Enter>", lambda event, w=widget: on_enter(event, w))
    widget.bind("<Leave>", lambda event, w=widget: on_leave(event, w))
    widget.bind("<Button-1>", lambda event, w=widget: on_click(event, w))

# Hàm đổi theme
def change_theme(theme_name):
    """Đổi giao diện dựa trên theme_name"""
    if theme_var.get() != theme_name:
        theme_var.set(theme_name)  # Cập nhật biến theme nếu cần

    # Định nghĩa màu theo theme
    theme_colors = {
        "Dark": {"bg": "black", "fg": "white", "highlight": "yellow"},
        "Light": {"bg": "#dddddd", "fg": "black", "highlight": "blue"},
        "Blue": {"bg": "#66b1ff", "fg": "white", "highlight": "black"}
    }

    # Lấy màu tương ứng với theme (mặc định là Light nếu không tìm thấy)
    colors = theme_colors.get(theme_name, theme_colors["Light"])

    # Cập nhật nền cho root
    root.config(bg=colors["bg"])

    # Danh sách các widget cần đổi màu
    widgets = [
        logo_label, made_with_label, copyright_label, support_label, 
        fromvietnam_label, copyright_c_label, vi_label, 
        en_label, zh_label, es_label, jp_label
    ]

    # Kiểm tra widget trước khi cập nhật (tránh lỗi nếu chưa khởi tạo)
    for widget in widgets:
        if widget.winfo_exists():
            widget.config(bg=colors["bg"], fg=colors["fg"])

    # Các widget có màu đặc biệt
    if freebird_label.winfo_exists():
        freebird_label.config(bg=colors["bg"], fg=colors["highlight"])
    if email_text_label.winfo_exists():
        email_text_label.config(bg=colors["bg"], fg=colors["fg"])
    if email_label.winfo_exists():
        email_label.config(bg=colors["bg"], fg=colors["highlight"])

    # Cập nhật màu cho FRAME - Using language_section_frame instead of language_choose_frame
    for frame in [footer_frame, flag_menu_frame, content_frame, theme_section_frame, language_section_frame, selections_frame]:
        if frame.winfo_exists():
            frame.config(bg=colors["bg"])
            frame.update_idletasks()  # Cập nhật lại giao diện ngay

    # Cập nhật Style của Radiobutton
    style.configure(
        "Custom.TRadiobutton",
        background=colors["bg"],    
        foreground=colors["fg"],    
        font=("Segoe UI", 10),
        indicatorbackground=colors["bg"],  
        indicatorcolor=colors["highlight"]  
    )

    # Cập nhật màu sắc cho tất cả Radiobutton trong theme_section_frame
    for child in theme_section_frame.winfo_children():
        if isinstance(child, ttk.Radiobutton):  
            child.config(style="Custom.TRadiobutton")

    # Cập nhật style cho Language.TRadiobutton
    style.configure(
        "Language.TRadiobutton",
        background=colors["bg"],
        foreground=colors["fg"],
        font=("Segoe UI", 10),
        indicatorbackground=colors["bg"],  
        indicatorcolor=colors["highlight"]  
    )
    # Cập nhật màu sắc cho tất cả Radiobutton trong theme_section_frame
    for child in language_section_frame.winfo_children():
        if isinstance(child, ttk.Radiobutton):  
            child.config(style="Language.TRadiobutton")

    # Cập nhật màu cho language_section_frame
    language_section_frame.configure(bg=colors["bg"])

    # Kiểm tra logo_label có hình ảnh không?
    if logo_label.winfo_exists():
        if logo_label.cget("image") == "":  
            logo_label.config(bg=colors["bg"], fg=colors["fg"])  # Chỉ đổi màu nếu không có ảnh
        else:
            logo_label.config(fg=colors["fg"])  # Giữ ảnh nền, chỉ đổi màu chữ


    


# Hàm mở tab Split
def open_split_tab(event=None):
    notebook.select(split_tab)  # Chuyển sang tab split_tab

# Hàm mở tab Merge
def open_merge_tab(event=None):
    notebook.select(merge_tab)  # Chuyển sang tab merge_tab



# Current page number
global current_page_number
current_page_number = 1




def parse_page_ranges(page_ranges, total_pages):
    valid_page_numbers = set()

    for part in page_ranges.split(','):
        part = part.strip()
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                if start > end or start < 1 or end > total_pages:
                    raise ValueError(f"{translate('error')}: Invalid range '{part}'")
                valid_page_numbers.update(range(start - 1, end))  # Convert to 0-based
            except ValueError:
                messagebox.showerror(translate("error"), f"{translate('error')}: Invalid range '{part}'")
        else:
            try:
                page = int(part)
                if page < 1 or page > total_pages:
                    raise ValueError(f"{translate('error')}: Page '{part}' is out of range")
                valid_page_numbers.add(page - 1)  # Convert to 0-based
            except ValueError:
                messagebox.showerror(translate("error"), f"{translate('error')}: Invalid page '{part}'")

    return sorted(valid_page_numbers)



#fun tách file   
def split_pdf(input_pdf_path, output_folder, page_ranges, save_as_single):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    with open(input_pdf_path, 'rb') as infile:
        reader = PyPDF2.PdfReader(infile)
        total_pages = len(reader.pages)

        page_numbers = parse_page_ranges(page_ranges, total_pages)
        if not page_numbers:
            messagebox.showerror(translate("error"), f"{translate('error')}: No valid pages to process.")
            return

        if save_as_single:
            writer = PyPDF2.PdfWriter()
            for page_number in page_numbers:
                writer.add_page(reader.pages[page_number])

            output_pdf_path = os.path.join(output_folder, "merged_output.pdf")
            with open(output_pdf_path, 'wb') as outfile:
                writer.write(outfile)

            messagebox.showinfo(translate("success"), f"All selected pages saved as {output_pdf_path}")
        else:
            for page_number in page_numbers:
                writer = PyPDF2.PdfWriter()
                writer.add_page(reader.pages[page_number])

                output_pdf_path = os.path.join(output_folder, f"page_{page_number + 1}.pdf")
                with open(output_pdf_path, 'wb') as outfile:
                    writer.write(outfile)

            messagebox.showinfo(translate("success"), f"Pages successfully saved in {output_folder}")



def display_pdf_info(pdf_path):
    print(f"Displaying info for {pdf_path}")
    
    
def select_input_pdf():
    # Mở hộp thoại để người dùng chọn file PDF
    input_pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    
    if (input_pdf_path):  # Nếu người dùng chọn file
        # Cập nhật ô nhập liệu (input_pdf_entry) với đường dẫn file
        input_pdf_entry.delete(0, tk.END)
        input_pdf_entry.insert(0, input_pdf_path)
        
        # Lưu trạng thái hiện tại
        save_state()
        
        # Hiển thị thông tin về PDF (thông qua hàm display_pdf_info)
        display_pdf_info(input_pdf_path)
        
        # Chuyển đến tab split_tab ngay lập tức
        notebook.select(split_tab)
    else:
        print("No file selected.")  # Thông báo nếu không có file nào được chọn
        # Ẩn nút Previous và Next nếu không có tệp PDF được chọn
        previous_page_button.grid_remove()
        next_page_button.grid_remove()
        
        
def select_output_folder():
    output_folder = filedialog.askdirectory()
    output_folder_entry.delete(0, tk.END)
    output_folder_entry.insert(0, output_folder)
    save_state()  # Lưu lại trạng thái mới sau khi thay đổi


def on_split_button_click():
    input_pdf_path = input_pdf_entry.get()
    output_folder = output_folder_entry.get()
    page_ranges = page_ranges_entry.get()
    save_as_single = save_as_single_var.get()

    if not input_pdf_path or not output_folder or not page_ranges:
        messagebox.showerror(translate("error"), translate("error"))
        return

    split_pdf(input_pdf_path, output_folder, page_ranges, save_as_single)

#fun gộp file    
def merge_pdfs(input_pdf_paths, output_pdf_path):
    """
    Merge multiple PDFs into one PDF file.
    
    :param input_pdf_paths: List of paths to the input PDFs.
    :param output_pdf_path: Path to save the merged PDF.
    """
    if not input_pdf_paths:
        messagebox.showerror("Error", "Please select at least one PDF file to merge.")
        return

    writer = PyPDF2.PdfWriter()
    
    for pdf_path in input_pdf_paths:
        try:
            with open(pdf_path, 'rb') as infile:
                reader = PyPDF2.PdfReader(infile)
                for page in range(len(reader.pages)):
                    writer.add_page(reader.pages[page])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to merge {pdf_path}: {e}")
            return
    
    with open(output_pdf_path, 'wb') as outfile:
        writer.write(outfile)
    
    messagebox.showinfo("Success", f"PDFs merged successfully! Saved as {output_pdf_path}")

# Hàm chọn các tệp PDF đầu vào
def select_input_pdfs_for_merge():
    input_pdfs = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
    if input_pdfs:
        # Hiển thị danh sách tệp PDF vào ô nhập liệu
        input_pdfs_entry.delete(0, tk.END)  # Xóa nội dung cũ
        input_pdfs_entry.insert(0, ', '.join(input_pdfs))  # Chèn danh sách tệp
        save_state()  # Lưu lại trạng thái mới sau khi thay đổi
        # Tự động chuyển tab
        notebook.select(merge_tab)

        # Hiển thị preview của các PDF đã chọn
        preview_multiple_pdfs(input_pdfs)
        # Hiển thị phần preview nếu có tệp
        preview_frame.grid(row=2, column=0, columnspan=3, pady=10)

        # Hiển thị các nút "Select All" và "Unselect All" khi có thumbnail
        select_all_button.grid(row=4, column=0, padx=10, pady=5)
        unselect_button.grid(row=4, column=1, padx=10, pady=5)
    else:
        # Ẩn phần preview nếu không có tệp PDF
        preview_frame.grid_forget()

        # Ẩn các nút "Select All" và "Unselect All" nếu không có thumbnail
        select_all_button.grid_forget()
        unselect_button.grid_forget()


# Hàm chọn tệp PDF đầu ra
def select_output_pdf_for_merge():
    output_pdf = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
    output_pdf_entry.delete(0, tk.END)
    output_pdf_entry.insert(0, output_pdf)
    save_state()  # Lưu lại trạng thái mới sau khi thay đổi



# Hàm xử lý sự kiện khi nhấn nút "Merge"
def on_merge_button_click():
    # Kiểm tra xem có tệp nào được tick không, nếu không thì mặc định gộp tất cả
    if not selected_pdfs_to_merge:
        # Nếu không có tệp nào được chọn qua checkbox, thêm tất cả các tệp vào danh sách để gộp
        selected_pdfs_to_merge.extend([file_path for file_path, var in selected_pdfs if var.get() == 1])

    if not selected_pdfs_to_merge:
        messagebox.showerror("Error", "Please select at least one PDF file to merge.")
        return

    # Đường dẫn tệp đã chọn
    output_pdf = output_pdf_entry.get()

    merge_pdfs(selected_pdfs_to_merge, output_pdf)



def preview_pdf_page(file_path, page_number):
    try:
        # Đọc trang PDF
        pdf_document = fitz.open(file_path)
        if page_number < 1 or page_number > len(pdf_document):
            raise ValueError(f"{translate('error')}: Invalid page number.")

        # Chuyển trang PDF thành ảnh
        pdf_page = pdf_document[page_number - 1]
        pix = pdf_page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Hiển thị ảnh trong giao diện Tkinter
        img.thumbnail((300, 400))  # Điều chỉnh kích thước hình ảnh
        img_tk = ImageTk.PhotoImage(img)
        pdf_preview_label.config(image=img_tk)
        pdf_preview_label.image = img_tk  # Giữ tham chiếu để không bị xóa

        pdf_document.close()
    except Exception as e:
        messagebox.showerror(translate("error"), str(e))
        
        

# Hàm hiển thị thumbnail cho trang đầu tiên của PDF
def preview_pdf_page_for_merge(file_path, page_number=1):
    """
    Hiển thị preview trang PDF đầu tiên dưới dạng hình ảnh
    :param file_path: Đường dẫn tệp PDF
    :param page_number: Số trang cần hiển thị (mặc định là trang đầu tiên)
    """
    try:
        # Mở tệp PDF
        pdf_document = fitz.open(file_path)
        
        # Lấy trang đầu tiên và chuyển thành ảnh
        pdf_page = pdf_document.load_page(page_number - 1)
        pix = pdf_page.get_pixmap()
        
        # Chuyển pixmap thành ảnh và điều chỉnh kích thước
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.thumbnail((200, 250))  # Điều chỉnh kích thước thumbnail
        img_tk = ImageTk.PhotoImage(img)
        
        return img_tk

    except Exception as e:
        messagebox.showerror("Lỗi", str(e))  # Hiển thị lỗi nếu có

# Hàm hiển thị các preview của nhiều tệp PDF
def preview_multiple_pdfs(file_paths):
    """
    Hiển thị preview trang đầu tiên của nhiều file PDF
    :param file_paths: Danh sách các tệp PDF
    """
    # Xóa các thumbnail cũ trước khi thêm mới
    for widget in thumbnail_frame.winfo_children():
        widget.grid_forget()

    column = 0  # Khởi tạo biến column tại đây
    global selected_pdfs
    selected_pdfs = []  # Danh sách các tệp đã được chọn
    
    for thumbnail_number, file_path in enumerate(file_paths, 1):
        img_tk = preview_pdf_page_for_merge(file_path)
        
        # Hiển thị thumbnail
        label = tk.Label(thumbnail_frame, image=img_tk)
        label.image = img_tk  # Giữ tham chiếu ảnh
        label.grid(row=0, column=column, padx=5, pady=5)  # Đặt các thumbnail theo chiều ngang

        # Hiển thị thông tin tệp dưới thumbnail
        display_pdf_info_for_thumbnail(file_path, column, thumbnail_number)  # Cập nhật để truyền `column`

        # Checkbox cho phép chọn tệp PDF
        var = tk.IntVar(value=1)  # Đặt giá trị mặc định là 1 (checked)
        check_button = tk.Checkbutton(thumbnail_frame, variable=var, command=lambda f=file_path, v=var: toggle_pdf_selection(f, v))
        check_button.grid(row=2, column=column, padx=5, pady=5)

        # Lưu trữ checkbox đã chọn
        selected_pdfs.append((file_path, var))

        column += 1  # Tăng cột sau mỗi thumbnail

    # Cập nhật kích thước canvas
    thumbnail_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    
# Hàm chọn tất cả các tệp PDF
def select_all_pdfs():
    for file_path, var in selected_pdfs:
        var.set(1)  # Đánh dấu tất cả các checkbox
        if file_path not in selected_pdfs_to_merge:
            selected_pdfs_to_merge.append(file_path)
# Hàm bỏ chọn tất cả các tệp PDF
def unselect_all_pdfs():
    for file_path, var in selected_pdfs:
        var.set(0)  # Bỏ đánh dấu tất cả các checkbox
    selected_pdfs_to_merge.clear()  # Xóa danh sách tệp đã chọn
# Hàm thay đổi trạng thái chọn tệp PDF
def toggle_pdf_selection(file_path, var):
    if var.get() == 1:
        # Thêm tệp vào danh sách các tệp đã chọn
        if file_path not in selected_pdfs_to_merge:
            selected_pdfs_to_merge.append(file_path)
    else:
        # Xóa tệp khỏi danh sách các tệp đã chọn
        if file_path in selected_pdfs_to_merge:
            selected_pdfs_to_merge.remove(file_path)





        
        



        
# Hàm hiển thị thông tin về tệp PDF dưới thumbnail
def display_pdf_info_for_thumbnail(file_path, column, thumbnail_number):
    """
    Hiển thị thông tin về tệp PDF dưới thumbnail
    :param file_path: Đường dẫn tệp PDF
    :param column: Cột hiện tại
    :param thumbnail_number: Số thứ tự của thumbnail
    """
    try:
        # Lấy thông tin tệp
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Đổi kích thước sang MB
        file_name = os.path.basename(file_path)
        with open(file_path, 'rb') as infile:
            reader = PyPDF2.PdfReader(infile)
            total_pages = len(reader.pages)

        # Hiển thị tên tệp và thông tin
        info_label = tk.Label(thumbnail_frame, text=f"{file_name}\n{total_pages} Pages\n{file_size:.2f} MB\n{thumbnail_number}",
                              font=("Segoe UI", 8), anchor="n", justify="center")
        info_label.grid(row=1, column=column, padx=5, pady=5)

    except Exception as e:
        messagebox.showerror("Lỗi", f"Could not read file file: {str(e)}")
        




def show_previous_page():
    global current_page_number
    if current_page_number > 1:
        current_page_number -= 1
        preview_pdf_page(input_pdf_entry.get(), current_page_number)
        update_navigation_buttons

    # Cập nhật trạng thái nút
    previous_page_button.config(state="normal" if current_page_number > 1 else "disabled")
    next_page_button.config(state="normal")


def show_next_page():
    global current_page_number
    input_pdf_path = input_pdf_entry.get()
    try:
        pdf_document = fitz.open(input_pdf_path)
        total_pages = len(pdf_document)
        pdf_document.close()
    except Exception as e:
        messagebox.showerror(translate("error"), str(e))
        return

    if current_page_number < total_pages:
        current_page_number += 1
        preview_pdf_page(input_pdf_path, current_page_number)
        update_navigation_buttons

    # Cập nhật trạng thái nút
    next_page_button.config(state="normal" if current_page_number < total_pages else "disabled")
    previous_page_button.config(state="normal")








def refresh_ui(notebook=None):
    """Update all UI elements with translations"""
    if not notebook:
        return
        
    try:
        # Update tab texts
        notebook.tab(split_tab, text=translate("split_pdf"))
        notebook.tab(merge_tab, text=translate("merge_pdf"))
        notebook.tab(imageeditor_tab, text=translate("image_editor"))
        
        # Update all UI elements
        widgets_to_update = {
            input_pdf_label: "select_pdf",
            output_folder_label: "select_output",
            page_ranges_label: "page_range",
            save_as_single_checkbox: "save_single",
            split_button: "split",
            input_pdfs_label: "select_pdfs",
            output_pdf_label: "select_output_merge",
            merge_button: "merge_button",
            support_label: "we_support",
            or_label: "or",
            previous_page_button: "previous_page",
            next_page_button: "next_page",
            convert_to_images_button: "convert_to_images",
            extract_text_button: "extract_text", 
            convert_to_word_button: "convert_to_word",
            encrypt_button: "encrypt_pdf",
            open_images_button: "open_images",
            images_content: "image_editor_text_content"
        }
        
        # Update text for all widgets
        for widget, key in widgets_to_update.items():
            if widget.winfo_exists():
                widget.config(text=translate(key))
        
        # Force update UI
        root.update_idletasks()
        
    except Exception as e:
        print(f"Error updating UI: {e}")

def refresh_all_tabs():
    """Refresh all open tabs when language changes"""
    try:
        # Lưu tab hiện tại
        current_tab = notebook.select()
        
        # Cập nhật text cho các tab chính
        notebook.tab(split_tab, text=translate("split_pdf"))
        notebook.tab(merge_tab, text=translate("merge_pdf"))
        notebook.tab(imageeditor_tab, text=translate("image_editor"))
        
        # Cập nhật tất cả các widget có text
        widgets_to_update = {
            input_pdf_label: "select_pdf",
            output_folder_label: "select_output",
            page_ranges_label: "page_range",
            save_as_single_checkbox: "save_single",
            split_button: "split",
            input_pdfs_label: "select_pdfs", 
            output_pdf_label: "select_output_merge",
            merge_button: "merge_button",
            input_pdf_button: "choose_file",
            output_folder_button: "choose_file", 
            input_pdfs_button: "choose_file",
            output_pdf_button: "choose_output",
            support_label: "we_support",
            copyright_label: "copyright",
            made_with_label: "made_with",
            previous_page_button: "previous_page",
            next_page_button: "next_page",
            open_images_button: "open_images",
            images_content: "image_editor_text_content"
        }
        
        # Cập nhật text cho tất cả widget
        for widget, translation_key in widgets_to_update.items():
            if widget.winfo_exists():
                widget.config(text=translate(translation_key))
        
        # Force update UI
        root.update_idletasks()
        
        # Chọn lại tab hiện tại
        if current_tab in notebook.tabs():
            notebook.select(current_tab)
            
    except Exception as e:
        print(f"Error refreshing UI: {e}")

def on_language_change(lang_code):
    """Handle language change and UI update"""
    global current_language, translations
    
    print(f"Changing language to: {lang_code}")
    
    # Cập nhật ngôn ngữ hiện tại
    current_language = lang_code
    
    # Load translations mới 
    translations = load_translations(lang_code)
    
    # Cập nhật UI
    refresh_all_tabs()
    
    # Cập nhật menu
    update_menu_translations()
    
    # Cập nhật radio buttons
    lang_var.set(lang_code)
    
    # Force update
    root.update_idletasks()
    
    print(f"Language changed to: {lang_code}")

def update_all_labels():
    """Update all labels with new translations"""
    # Cập nhật các tab
    notebook.tab(split_tab, text=translate("split_pdf"))
    notebook.tab(merge_tab, text=translate("merge_pdf"))
    notebook.tab(imageeditor_tab, text=translate("image_editor"))
    
    # Cập nhật các label trong split_tab
    input_pdf_label.config(text=translate("select_pdf"))
    output_folder_label.config(text=translate("select_output"))
    page_ranges_label.config(text=translate("page_range"))
    save_as_single_checkbox.config(text=translate("save_single"))
    split_button.config(text=translate("split"))
    
    # Cập nhật các label khác
    support_label.config(text=translate("we_support"))
    
    # Refresh giao diện
    root.update()

# Chuyen file PDF sang dinh dang anh
def convert_pdf_to_images(input_pdf_path, output_folder):
    try:
        pdf_document = fitz.open(input_pdf_path)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        for page_number in range(len(pdf_document)):
            page = pdf_document[page_number]
            pix = page.get_pixmap()
            output_image_path = os.path.join(output_folder, f"page_{page_number + 1}.png")
            pix.save(output_image_path)

        pdf_document.close()
        messagebox.showinfo(translate("success"), f"Images saved in {output_folder}")
    except Exception as e:
        messagebox.showerror(translate("error"), str(e))

#Chuyển PDF sang văn bản
def extract_text_from_pdf(input_pdf_path, output_folder):
    try:
        pdf_document = fitz.open(input_pdf_path)
        output_text_path = os.path.join(output_folder, "extracted_text.txt")

        with open(output_text_path, "w", encoding="utf-8") as text_file:
            for page in pdf_document:
                text = page.get_text()
                text_file.write(text + "\n\n")

        pdf_document.close()
        messagebox.showinfo(translate("success"), f"Text saved as {output_text_path}")
    except Exception as e:
        messagebox.showerror(translate("error"), str(e))

#Chuyển PDF sang Word
def convert_pdf_to_word(input_pdf_path, output_folder):
    try:
        pdf_document = fitz.open(input_pdf_path)
        doc = Document()
        output_word_path = os.path.join(output_folder, "output.docx")

        for page in pdf_document:
            text = page.get_text()
            doc.add_paragraph(text)

        doc.save(output_word_path)
        pdf_document.close()
        messagebox.showinfo(translate("success"), f"Word file saved as {output_word_path}")
    except Exception as e:
        messagebox.showerror(translate("error"), str(e))


#Hàm bảo mật file PDF
def encrypt_pdf(input_pdf_path, output_pdf_path, password):
    try:
        with open(input_pdf_path, 'rb') as infile:
            reader = PyPDF2.PdfReader(infile)
            writer = PyPDF2.PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            # Thiết lập mật khẩu
            writer.encrypt(password)

            # Ghi tệp PDF được mã hóa
            with open(output_pdf_path, 'wb') as outfile:
                writer.write(outfile)

        messagebox.showinfo(translate("success"), f"Encrypted PDF saved at: {output_pdf_path}")
    except Exception as e:
        messagebox.showerror(translate("error"), str(e))

#Hàm xử lý sự kiện khi nhấn nút mã hóa PDF
def on_encrypt_button_click():
    input_pdf_path = input_pdf_entry.get()
    output_folder = output_folder_entry.get()

    if not input_pdf_path or not output_folder:
        messagebox.showerror(translate("error"), translate("error"))
        return

    # Yêu cầu người dùng nhập mật khẩu
    password = simpledialog.askstring("Password", "Enter password for the PDF:", show="*")

    if not password:
        messagebox.showerror(translate("error"), "Password cannot be empty!")
        return

    # Đường dẫn lưu tệp PDF mã hóa
    output_pdf_path = os.path.join(output_folder, "encrypted_output.pdf")
    encrypt_pdf(input_pdf_path, output_pdf_path, password)





# Create the main Tkinter window
root = tk.Tk()
root.title("Free Bird")
# Đặt biểu tượng cho cửa sổ
icon = PhotoImage(file=r"images/icon.png")
root.iconphoto(True, icon)
root.configure(bg="#dddddd")  # Màu nền tối cho cửa sổ chính
# Thay đổi font mặc định cho tất cả các widget
root.option_add("*Font", ("Segoe UI", 11))
settings = load_settings()  # Gọi hàm load_settings từ settings.py
# Cấu hình root để co giãn hàng và cột chứa Notebook
root.minsize(1000, 600)  # Đặt kích thước tối thiểu (850x700)

root.grid_rowconfigure(2, weight=1)  # Cho phép hàng 2 mở rộng
root.grid_columnconfigure(0, weight=1)  # Cột 0 cũng mở rộng


# Create the notebook first
notebook = ttk.Notebook(root)
notebook.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

# Create tabs
split_tab = ttk.Frame(notebook)
merge_tab = ttk.Frame(notebook)
imageeditor_tab = ttk.Frame(notebook)

# Add tabs to notebook
notebook.add(split_tab, text=translate("split_pdf"))
notebook.add(merge_tab, text=translate("merge_pdf"))
notebook.add(imageeditor_tab, text=translate("image_editor"))

# Now configure the style
style = ttk.Style()

# Configure consistent colors
COLORS = {
    'tab_bg': "#ffffff",          # Tab background
    'tab_active': "#4a90e2",      # Active tab
    'tab_hover': "#87CEEB",       # Hover state
    'frame_bg': "#f5f5f5",        # Inner frame background
    'label_bg': "#f5f5f5",        # Label background
    'button_bg': "#e0e0e0",       # Button background
    'entry_bg': "#ffffff",        # Entry background
    'border': "#d0d0d0"          # Border color
}

# Configure Notebook style with consistent colors
style.configure("TNotebook", 
    background=COLORS['frame_bg'],
    borderwidth=3,
    relief="groove",
    padding=5
)

style.configure("TNotebook.Tab",
    background=COLORS['tab_bg'],
    padding=[20, 12],
    font=("Segoe UI", 12, "bold"),
    borderwidth=2,
    relief="solid",
    bordercolor=COLORS['border']
)

# Configure frame style
style.configure("TabFrame.TFrame",
    background=COLORS['frame_bg'],
    relief="solid",
    borderwidth=1,
    bordercolor=COLORS['border']
)

# Function to apply consistent styling to widgets
def apply_widget_styles(parent):
    for child in parent.winfo_children():
        if isinstance(child, tk.Label):
            child.configure(
                background=COLORS['frame_bg'],
                relief="flat"
            )
        elif isinstance(child, tk.Entry):
            child.configure(
                background=COLORS['entry_bg'],
                relief="solid",
                borderwidth=1
            )
        elif isinstance(child, tk.Button):
            child.configure(
                background=COLORS['button_bg'],
                relief="solid",
                borderwidth=1,
                activebackground=COLORS['tab_hover']
            )
        elif isinstance(child, ttk.Frame):
            child.configure(style="TabFrame.TFrame")
            apply_widget_styles(child)  # Recursively apply to nested frames
        elif isinstance(child, tk.Frame):
            child.configure(
                background=COLORS['frame_bg'],
                relief="flat"
            )
            apply_widget_styles(child)  # Recursively apply to nested frames

# After creating tabs, apply the consistent styling
for tab in [split_tab, merge_tab, imageeditor_tab]:
    tab.configure(style="TabFrame.TFrame")
    apply_widget_styles(tab)

# Update specific widgets that need different styling
def update_special_widgets():
    # Update preview frame
    if 'preview_frame' in globals():
        preview_frame.configure(background=COLORS['frame_bg'])
        canvas.configure(background=COLORS['frame_bg'])
        thumbnail_frame.configure(background=COLORS['frame_bg'])
    
    # Update file info frame
    if 'file_info_frame' in globals():
        file_info_frame.configure(background=COLORS['frame_bg'])
        file_info_label.configure(background=COLORS['frame_bg'])

# Call this after creating all widgets
update_special_widgets()

# Add custom class for rounded corners
class RoundedNotebook(ttk.Notebook):
    def __init__(self, parent, radius=15, **kwargs):
        ttk.Notebook.__init__(self, parent, **kwargs)
        
        self.style = ttk.Style()
        self.style.element_create('Custom.Notebook.Border', 'from', 'default')
        self.style.layout('Custom.TNotebook', [
            ('Custom.Notebook.Border', {
                'sticky': 'nswe',
                'border': 20,     # Increased border space
                'children': [
                    ('Notebook.Client', {'sticky': 'nswe'})
                ]
            })
        ])
        
        # Configure custom style with rounded corners
        self.style.configure('Custom.TNotebook',
            background='#e0e0e0',
            borderwidth=3,
            padding=10,
            tabmargins=[5, 5, 2, 0],  # [left, top, right, bottom]
            tabposition='n'
        )
        
        self.configure(style='Custom.TNotebook')

# Replace notebook creation with RoundedNotebook
notebook = RoundedNotebook(root, radius=20)  # Increased radius for more rounded corners
notebook.grid(row=2, column=0, padx=25, pady=15, sticky="nsew")  # Increased padding

# Add shadow effect to tabs
def add_tab_shadow(tab):
    shadow_color = "#00000022"  # Semi-transparent black
    tab.configure(style="Shadow.TFrame")
    style.configure("Shadow.TFrame",
        background="white",
        relief="solid",
        borderwidth=1,
        highlightthickness=1,
        highlightbackground=shadow_color,
        highlightcolor=shadow_color
    )

# Apply shadow and style to each tab
for tab in [split_tab, merge_tab, imageeditor_tab]:
    add_tab_shadow(tab)
    tab.configure(style='Custom.TFrame')
    # Add padding to tab content
    for child in tab.winfo_children():
        child.grid_configure(padx=8, pady=8)  # Consistent internal padding

# Create the Menu Bar with custom style
root.option_add('*tearOff', False)  # Disable tear-off menus
# Tăng kích thước font từ 9 lên 11 cho menu bar chính và menu con
menu_font = ("Segoe UI", 10)  # Set font size to 11
# Create the Menu Bar with custom style
root.option_add('*tearOff', False)  # Disable tear-off menus
menu_bar = tk.Menu(root, font=menu_font, bg="white", fg="black")
root.config(menu=menu_bar)

# Hàm tạo menu con với style dùng chung
def create_menu(parent, tearoff=0): 
    menu = tk.Menu(
        parent,
        font=menu_font,
        bg="white",
        fg="black",
        activebackground="#D7ECFF",
        activeforeground="black",
        tearoff=tearoff  #Áp dụng tearoff
    )
    return menu 

# File Menu
file_menu = create_menu(menu_bar)
file_menu.add_command(label="Split PDF File", command=select_input_pdf)
file_menu.add_command(label="Merge PDF Files", command=select_input_pdfs_for_merge)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)
menu_bar.add_cascade(label="File", menu=file_menu, font=menu_font)

# Settings Menu 
settings_menu = create_menu(menu_bar)
settings_menu.add_command(label="Settings", command=lambda: open_settings_and_switch_tab(notebook))
menu_bar.add_cascade(label="Settings", menu=settings_menu, font=menu_font)

# Edit Menu
edit_menu = create_menu(menu_bar)
edit_menu.add_command(label="Undo", command=undo)
edit_menu.add_command(label="Clear All", command=clear_all)
menu_bar.add_cascade(label="Edit", menu=edit_menu, font=menu_font)

# Theme Menu
# Biến lưu giao diện được chọn
theme_var = tk.StringVar(value="Light")  # Mặc định là Light Theme
# Danh sách theme
themes = {
    "Dark Theme": "Dark",
    "Light Theme": "Light",
    "Blue Theme": "Blue"
}
# Hàm cập nhật theme khi giá trị theme_var thay đổi
def update_theme(*args):
    change_theme(theme_var.get())
# Theo dõi sự thay đổi của theme_var để gọi change_theme() tự động
theme_var.trace_add("write", update_theme)
# Tạo menu theme
theme_menu = create_menu(menu_bar)
# Thêm các lựa chọn vào menu
for theme_name, theme_code in themes.items():
    theme_menu.add_radiobutton(label=theme_name, variable=theme_var, value=theme_code)

menu_bar.add_cascade(label="Theme", menu=theme_menu, font=menu_font)
root.config(menu=menu_bar)



# Language Menu
def on_language_change(lang_code):
    """Handle language change and UI update"""
    change_language(lang_code)
    refresh_ui(notebook)  # Pass notebook explicitly

# Language Menu
language_menu = create_menu(menu_bar)
language_menu.add_command(label="Tiếng Việt", command=lambda: on_language_change("vi"))
language_menu.add_command(label="English", command=lambda: on_language_change("en"))
language_menu.add_command(label="中文", command=lambda: on_language_change("zh"))
language_menu.add_command(label="Español", command=lambda: on_language_change("es"))
language_menu.add_command(label="日本語", command=lambda: on_language_change("jp"))
menu_bar.add_cascade(label="Language", menu=language_menu, font=menu_font)

# Help Menu
help_menu = create_menu(menu_bar)
help_menu.add_command(label="About", command=lambda: show_about_page(notebook))
help_menu.add_command(label="Help Contents", command=lambda: messagebox.showinfo("Help", "Help contents not available"))
help_menu.add_command(label="Software Update", command=lambda: open_software_update_tab(notebook))
menu_bar.add_cascade(label="Help", menu=help_menu, font=menu_font)



# 1. Logo Section (Left side)
##########################
# Mở ảnh và thay đổi kích thước
img = Image.open("images/dove.png").resize((250, 160), Image.LANCZOS)
img = img.convert("RGBA")
logo = ImageTk.PhotoImage(img)
logo_label = tk.Label(root, image=logo, bg="#dddddd")
logo_label.image = logo
logo_label.grid(row=0, column=0, padx=10, pady=2, sticky="w")

# 2. Language Variable
##########################
lang_var = tk.StringVar(value="vi")
lang_var.trace_add("write", lambda *args: on_language_change(lang_var.get()))

# 3. Language Selection (Right side, top)
##########################
flag_menu_frame = tk.Frame(root, bg="#dddddd")
flag_menu_frame.grid(row=0, column=0, padx=10, pady=5, sticky="E")

support_label = tk.Label(flag_menu_frame, text="WE SUPPORT", font=("Segoe UI", 11), bg="#dddddd")
support_label.grid(row=0, column=0, columnspan=5, pady=2)

# Flag images loading
try:
    flag_images = {
        "vi": ImageTk.PhotoImage(Image.open(r"images\vietnam_flag.png").resize((30, 20))),
        "en": ImageTk.PhotoImage(Image.open(r"images\uk_flag.png").resize((30, 20))),
        "zh": ImageTk.PhotoImage(Image.open(r"images\china_flag.png").resize((30, 20))),
        "es": ImageTk.PhotoImage(Image.open(r"images\Spanish_flag.png").resize((30, 20))),
        "jp": ImageTk.PhotoImage(Image.open(r"images\japan_flag.png").resize((30, 20))),
    }
except FileNotFoundError as e:
    print(f"Lỗi: Không tìm thấy hình ảnh. {e}")
    root.destroy()
    exit()

# Flag buttons and labels
vi_button = tk.Button(
    flag_menu_frame, 
    image=flag_images["vi"], 
    command=lambda: change_language("vi"),
    borderwidth=0, 
    highlightthickness=0
)
vi_button.grid(row=1, column=0, padx=15)
vi_label = tk.Label(flag_menu_frame, text="Tiếng Việt", font=("Segoe UI", 10), bg="#dddddd")
vi_label.grid(row=2, column=0)

en_button = tk.Button(
    flag_menu_frame,
    image=flag_images["en"],
    command=lambda: change_language("en"),
    borderwidth=0,
    highlightthickness=0
)
en_button.grid(row=1, column=1, padx=15) 
en_label = tk.Label(flag_menu_frame, text="English", font=("Segoe UI", 10), bg="#dddddd")
en_label.grid(row=2, column=1)

zh_button = tk.Button(flag_menu_frame, image=flag_images["zh"], command=lambda: change_language("zh"), borderwidth=0, highlightthickness=0)
zh_button.grid(row=1, column=2, padx=15)
zh_label = tk.Label(flag_menu_frame, text="中文", font=("Segoe UI", 10), bg="#dddddd")
zh_label.grid(row=2, column=2)

es_button = tk.Button(flag_menu_frame, image=flag_images["es"], command=lambda: change_language("es"), borderwidth=0, highlightthickness=0)
es_button.grid(row=1, column=3, padx=15)
es_label = tk.Label(flag_menu_frame, text="Español", font=("Segoe UI", 10), bg="#dddddd")
es_label.grid(row=2, column=3)

jp_button = tk.Button(flag_menu_frame, image=flag_images["jp"], command=lambda: change_language("jp"), borderwidth=0, highlightthickness=0)
jp_button.grid(row=1, column=4, padx=15)
jp_label = tk.Label(flag_menu_frame, text="日本語", font=("Segoe UI", 10), bg="#dddddd")
jp_label.grid(row=2, column=4)

"""
# Configure style for language Radiobuttons
style.configure(
    "Language.TRadiobutton",
    background="#dddddd",
    foreground="black",
    font=("Segoe UI", 10)
)

# Dictionary of language options
languages = {
    "Tiếng Việt": "vi",
    "English": "en", 
    "中文": "zh",
    "Español": "es",
    "日本語": "jp"
}


# Configure style for theme Radiobuttons
style.configure(
    "Custom.TRadiobutton",
    background="#dddddd",
    foreground="black",
    font=("Segoe UI", 10)
)

# Dictionary of language options
languages = {
    "Tiếng Việt": "vi",
    "English": "en", 
    "中文": "zh",
    "Español": "es",
    "日本語": "jp"
}
"""

style.configure(
    "Language.TRadiobutton",
    background="#dddddd",
    foreground="black",
    font=("Segoe UI", 10)
)

style.configure(
    "Custom.TRadiobutton", 
    background="#dddddd",
    foreground="black",
    font=("Segoe UI", 10)
)



# Create Radiobuttons for each language

# Update the existing language change function to handle Radiobuttons
def on_language_change(lang_code):
    """Handle language change and UI update"""
    global current_language
    current_language = lang_code
    translations = load_translations(lang_code)
    print(f"Selected language: {current_language}")
    refresh_ui(notebook)



# Create a frame containing language and theme selection
selections_frame = tk.Frame(root, bg="#dddddd")
selections_frame.grid(row=1, column=0, sticky="E", padx=20, pady=(0,5))  # Thay đổi pady từ (5,10) thành (0,5)

# Language Selection Frame FIRST
language_section_frame = tk.Frame(selections_frame, bg="#dddddd")
language_section_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=1, sticky="E")  # Giảm pady từ 2 xuống 1

# Language label - Bỏ bg cố định
tk.Label(
    language_section_frame,
    text="Language:",
    font=("Segoe UI", 10, "bold"),
    bg="#dddddd"

).grid(row=0, column=0, padx=(0,10), sticky="W")

# Language Radiobuttons - Bắt đầu từ column=1
languages = {
    "Tiếng Việt": "vi", 
    "English": "en", 
    "中文": "zh",
    "Español": "es",
    "日本語": "jp"
}
for col, (lang_name, lang_code) in enumerate(languages.items()):
    rb = ttk.Radiobutton(
        language_section_frame,
        text=lang_name,
        variable=lang_var,
        value=lang_code,
        style="Language.TRadiobutton",
        command=lambda c=lang_code: change_language(c)
    )
    rb.grid(row=0, column=col+1, padx=5)  # Thay đổi row=1 thành row=0 và column=col+1

# Theme Selection Frame
theme_section_frame = tk.Frame(selections_frame, bg="#dddddd")
theme_section_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=1, sticky="E")  # Giảm pady từ 2 xuống 1

# Theme label - Bỏ bg cố định
tk.Label(
    theme_section_frame,
    text="Theme:",
    font=("Segoe UI", 10, "bold"),
    bg="#dddddd"
).grid(row=0, column=0, padx=(0,10), sticky="W")

# Theme Radiobuttons - Bắt đầu từ column=1
themes = {"Light Theme": "Light", "Dark Theme": "Dark", "Blue Theme": "Blue"}
for col, (theme_name, theme_code) in enumerate(themes.items()):
    rb = ttk.Radiobutton(
        theme_section_frame,
        text=theme_name,
        variable=theme_var,
        value=theme_code,
        style="Custom.TRadiobutton",
    )
    rb.grid(row=0, column=col+1, padx=5)  # Thay đổi row=1 thành row=0 và column=col+1

# Create a Notebook (tabbed interface)
notebook = ttk.Notebook(root)
notebook.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")  # Co giãn theo kích thước cửa sổ

#Split PDF tab
split_tab = ttk.Frame(notebook)
notebook.add(split_tab, text=translate("split_pdf"))
# Cấu hình split_tab để nội dung bên trong có thể co giãn
split_tab.grid_rowconfigure(0, weight=1)
split_tab.grid_columnconfigure(0, weight=1)


# Create widgets
input_pdf_label = tk.Label(split_tab, text=translate("select_pdf"))
input_pdf_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
input_pdf_entry = tk.Entry(split_tab, width=50)
input_pdf_entry.grid(row=0, column=1)
input_pdf_button = tk.Button(split_tab, text=translate("choose_file"), command=select_input_pdf)
input_pdf_button.grid(row=0, column=2, padx=10, pady=10)

output_folder_label = tk.Label(split_tab, text=translate("select_output"))
output_folder_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
output_folder_entry = tk.Entry(split_tab, width=50)
output_folder_entry.grid(row=1, column=1)
output_folder_button = tk.Button(split_tab, text=translate("choose_output"), command=select_output_folder)
output_folder_button.grid(row=1, column=2, padx=10, pady=10)

page_ranges_label = tk.Label(split_tab, text=translate("page_range"))
page_ranges_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
page_ranges_entry = tk.Entry(split_tab, width=50)
page_ranges_entry.grid(row=2, column=1)

save_as_single_var = tk.BooleanVar()
save_as_single_checkbox = tk.Checkbutton(split_tab, text=translate("save_single"), variable=save_as_single_var)
save_as_single_checkbox.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="w")





#split_button
image = Image.open(r"icons\split.png")
image = image.resize((20, 20))
split_icon = ImageTk.PhotoImage(image)
split_button = tk.Button(
    split_tab,
    text=translate("split"),
    image=split_icon,
    compound='left',
    command=on_split_button_click,
    bg="#F0F0F0",   # Màu nền
    fg="black",     # Màu chữ
    font=("Segoe UI", 11, "bold"),
    width=110,        # Chiều rộng
    padx=10           # Khoảng cách giữa icon và text
)
split_button.grid(row=3, column=0, columnspan=3, pady=10)



or_label = tk.Label(split_tab, text=translate("or"), font=("Segoe UI", 11, "bold"))
or_label.grid(row=4, column=0, columnspan=3, sticky="we", padx=5, pady=5)

#người dùng chọn chức năng mã hóa PDF
image = Image.open(r"icons\encrypt.png")
image = image.resize((20, 20))
encrypt_icon = ImageTk.PhotoImage(image)
encrypt_button = tk.Button(
    split_tab,
    text=translate("encrypt_pdf"),
    image=encrypt_icon,
    compound='left',
    command=lambda: on_encrypt_button_click(),
    bg="#F0F0F0",   # Màu nền
    fg="black",     # Màu chữ
    font=("Segoe UI", 11, "bold"),
    width=110,        # Chiều rộng
    padx=10           # Khoảng cách giữa icon và text

)
encrypt_button.grid(row=5, column=0, columnspan=3, pady=10)
# Giữ tham chiếu đến icon để tránh bị thu hồi
encrypt_button.image = encrypt_icon



# Chuyển định dạng thành ảnh, qua text, qua word
button_frame = tk.Frame(split_tab)
button_frame.grid(row=6, column=0, columnspan=3, pady=10)


image = Image.open(r"icons\to_image.png")
image = image.resize((20, 20))
convert_to_images_icon = ImageTk.PhotoImage(image)
convert_to_images_button = tk.Button(
    button_frame,
    text=translate("convert_to_images"),
    image=convert_to_images_icon,
    compound='left',
    command=lambda: convert_pdf_to_images(input_pdf_entry.get(), output_folder_entry.get()),
    bg="#F0F0F0",   # Màu nền
    fg="black",     # Màu chữ
    font=("Segoe UI", 11, "bold"),
    width=220,        # Chiều rộng
    padx=10           # Khoảng cách giữa icon và text
)
convert_to_images_button.grid(row=0, column=0, padx=5, pady=5)



image = Image.open(r"icons\to_text.png")
image = image.resize((20, 20))
extract_text_icon = ImageTk.PhotoImage(image)
extract_text_button = tk.Button(
    button_frame,
    text=translate("extract_text"),
    image=extract_text_icon,
    compound='left',
    command=lambda: extract_text_from_pdf(input_pdf_entry.get(), output_folder_entry.get()),
    bg="#F0F0F0",   # Màu nền
    fg="black",     # Màu chữ
    font=("Segoe UI", 11, "bold"),
    width=220,        # Chiều rộng
    padx=10           # Khoảng cách giữa icon và text

)
extract_text_button.grid(row=0, column=1, padx=5, pady=5)






image = Image.open(r"icons\to_word.png")
image = image.resize((20, 20))
convert_to_word_icon = ImageTk.PhotoImage(image)
convert_to_word_button = tk.Button(
    button_frame,
    text=translate("convert_to_word"),
    image=convert_to_word_icon,
    compound='left',
    command=lambda: convert_pdf_to_word(input_pdf_entry.get(), output_folder_entry.get()),
    bg="#F0F0F0",   # Màu nền
    fg="black",     # Màu chữ
    font=("Segoe UI", 11, "bold"),
    width=220,        # Chiều rộng
    padx=10           # Khoảng cách giữa icon và text
)
convert_to_word_button.grid(row=0, column=2, padx=5, pady=5)



# Đảm bảo khung hình ảnh có kích thước cố định
pdf_preview_label = tk.Label(split_tab) 
pdf_preview_label.grid(row=0, column=3, rowspan=5, padx=10, pady=10)

# Frame chứa các nút điều hướng trang
page_nav_frame = tk.Frame(split_tab)
page_nav_frame.grid(row=6, column=3, pady=5)

# Ẩn nút sau khi tạo
previous_page_button = tk.Button(split_tab, text=translate("previous_page"), command=show_previous_page)
previous_page_button.grid(row=4, column=3, rowspan=2, padx=10, pady=15, sticky="w")
previous_page_button.grid_remove()  # Ẩn nút sau khi tạo

next_page_button = tk.Button(split_tab, text=translate("next_page"), command=show_next_page)
next_page_button.grid(row=4, column=3, rowspan=2, padx=10, pady=15, sticky="E")
next_page_button.grid_remove()  # Ẩn nút sau khi tạo






# Thêm khung thông tin file bên dưới khung Preview
file_info_frame = tk.Frame(split_tab)
file_info_frame.grid(row=7, column=3, rowspan=2, padx=10, pady=10, sticky="w")

# Nhãn hiển thị thông tin file
file_info_label = tk.Label(file_info_frame, text="", anchor="w", justify="left")
file_info_label.grid(row=8, column=0, padx=10, pady=5)




def create_page_navigation(total_pages):
    # Xóa các nút cũ nếu có
    for widget in page_nav_frame.winfo_children():
        widget.destroy()

    # Tạo nút Previous
    tk.Button(page_nav_frame, text=translate("previous_page"), command=show_previous_page).grid(row=0, column=0, padx=2)

    # Số nút trang hiển thị ở đầu và cuối
    start_pages = 4  # Số trang đầu
    end_pages = 2    # Số trang cuối

    # Tạo các nút số trang
    for page in range(1, total_pages + 1):
        # Hiển thị 4 trang đầu
        if page <= start_pages:
            btn = tk.Button(page_nav_frame, text=str(page),
                          command=lambda p=page: go_to_page(p))
            btn.grid(row=0, column=page, padx=2)
        
        # Hiển thị 2 trang cuối
        elif page > total_pages - end_pages:
            # Nếu có khoảng cách giữa nút cuối của 4 trang đầu và nút đầu của 2 trang cuối
            if page == total_pages - end_pages + 1 and page > start_pages + 1:
                # Thêm dấu ...
                tk.Label(page_nav_frame, text="...").grid(row=0, column=start_pages + 1, padx=2)
            
            btn = tk.Button(page_nav_frame, text=str(page),
                          command=lambda p=page: go_to_page(p))
            btn.grid(row=0, column=page + 1, padx=2)  # +1 để tính cả dấu ...

    # Tạo nút Next
    tk.Button(page_nav_frame, text=translate("next_page"), command=show_next_page).grid(row=0, column=total_pages + 2, padx=2)


def go_to_page(page_num):
    global current_page_number
    current_page_number = page_num
    preview_pdf_page(input_pdf_entry.get(), current_page_number)
    update_navigation_buttons()

def update_navigation_buttons():
    input_pdf_path = input_pdf_entry.get()
    try:
        pdf_document = fitz.open(input_pdf_path)
        total_pages = len(pdf_document)
        pdf_document.close()
        
        previous_page_button.config(state="normal" if current_page_number > 1 else "disabled")
        next_page_button.config(state="normal" if current_page_number < total_pages else "disabled")
    except Exception as e:
        print(f"Error updating navigation buttons: {e}")



# Hiển thị thông tin về file PDF
def display_pdf_info(file_path):
    global current_page_number
    try:
        # Khởi tạo giá trị mặc định cho các thông tin
        file_size = "N/A"
        file_name = "N/A"
        created_time = "N/A"
        total_pages = "N/A"

        # Kiểm tra nếu file tồn tại và lấy thông tin
        if os.path.exists(file_path):
            # Lấy thông tin file
            file_name = os.path.basename(file_path)
            try:
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # Đổi từ byte sang MB
            except:
                file_size = "N/A"
            try:
                created_time = time.ctime(os.path.getctime(file_path))  # Lấy thời gian tạo file
            except:
                created_time = "N/A"
            try:
                with open(file_path, 'rb') as infile:
                    reader = PyPDF2.PdfReader(infile)
                    total_pages = len(reader.pages)
                    # Tạo thanh điều hướng trang
                    create_page_navigation(total_pages)
            except:
                total_pages = "N/A"
        
        # Cập nhật nhãn thông tin file
        file_info_label.config(
            text=(
                f"{translate('file_info')}:\n"
                f"{translate('file_name')}: {file_name}\n"
                f"{translate('file_size')}: {file_size} MB\n"
                f"{translate('file_pages')}: {total_pages}\n"
                f"{translate('created')}: {created_time}"
            )
        )

        # Đặt trang đầu tiên khi hiển thị thông tin
        current_page_number = 1
        preview_pdf_page(file_path, current_page_number)

        # Hiển thị nút Previous và Next Page
        previous_page_button.grid()
        next_page_button.grid()

        # Vô hiệu hóa nút "Previous Page" nếu đang ở trang đầu tiên
        previous_page_button.config(state="disabled")
        # Kích hoạt nút "Next Page" nếu có nhiều hơn 1 trang
        next_page_button.config(state="normal" if total_pages != "N/A" and total_pages > 1 else "disabled")
        
    except Exception as e:
        file_info_label.config(text=translate("file_info"))
        messagebox.showinfo(translate("info"), translate("no_file_info"))





root.grid_columnconfigure(0, weight=1)
# Merge PDF tab
merge_tab = ttk.Frame(notebook)
notebook.add(merge_tab, text=translate("merge_pdf"))
# Cấu hình merge_tab để nội dung bên trong có thể co giãn
merge_tab.grid_rowconfigure(0, weight=1)
merge_tab.grid_columnconfigure(0, weight=1)

# Input PDF Files (Merge PDF)
input_pdfs_label = tk.Label(merge_tab, text=translate("select_pdfs"))
input_pdfs_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")  # Giảm padding
input_pdfs_entry = tk.Entry(merge_tab, width=40)
input_pdfs_entry.grid(row=0, column=1, padx=5, pady=5)  # Giảm padding
input_pdfs_button = tk.Button(merge_tab, text=translate("choose_file"), command=select_input_pdfs_for_merge)
input_pdfs_button.grid(row=0, column=2, padx=5, pady=5)  # Giảm padding

# Output PDF (Merge PDF)
output_pdf_label = tk.Label(merge_tab, text=translate("select_output_merge"))
output_pdf_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")  # Giảm padding
output_pdf_entry = tk.Entry(merge_tab, width=40)
output_pdf_entry.grid(row=1, column=1, padx=5, pady=5)  # Giảm padding
output_pdf_button = tk.Button(merge_tab, text=translate("choose_output"), command=select_output_pdf_for_merge)
output_pdf_button.grid(row=1, column=2, padx=5, pady=5)  # Giảm padding
# Merge Button
image = Image.open(r"icons\merge.png")
image = image.resize((20, 20))
merge_icon = ImageTk.PhotoImage(image)
merge_button = tk.Button(
    merge_tab,
    text=translate("merge_button"),
    image=merge_icon,
    compound='left',
    command=on_merge_button_click,
bg="#F0F0F0",   # Màu nền
    fg="black",     # Màu chữ
    font=("Segoe UI", 11, "bold"),
    width=130,        # Chiều rộng
    padx=10           # Khoảng cách giữa icon và text 
)
merge_button.grid(row=5, column=0, columnspan=3, pady=10, sticky='')  # Không dùng sticky='ew'






# Tạo một Frame để chứa cả hai nút
button_frame = tk.Frame(merge_tab)
button_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky='w')

# Nút "Select All"
select_all_button = tk.Button(button_frame, text="Select All", command=select_all_pdfs)
select_all_button.grid(row=0, column=0, padx=5, pady=5)
select_all_button.grid_forget()  # Ẩn nút khi không có thumbnail

# Nút "Unselect"
unselect_button = tk.Button(button_frame, text="Unselect", command=unselect_all_pdfs)
unselect_button.grid(row=0, column=1, padx=5, pady=5)
unselect_button.grid_forget()  # Ẩn nút khi không có thumbnail






# Frame chứa preview thumbnails
preview_frame = tk.Frame(merge_tab)

# Tạo canvas và scrollbar để chứa các thumbnail của PDF
frame = tk.Frame(preview_frame)
frame.pack(padx=10, pady=10)

canvas = tk.Canvas(frame, width=950, height=380)  # Thay đổi chiều cao của canvas
canvas.grid(row=0, column=0)

scrollbar = tk.Scrollbar(frame, orient="horizontal", command=canvas.xview)  # Scrollbar ngang
scrollbar.grid(row=1, column=0, sticky="ew")

canvas.config(xscrollcommand=scrollbar.set)

# Frame chứa các thumbnail
thumbnail_frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=thumbnail_frame, anchor="nw")

# Danh sách chứa các tệp đã chọn để gộp
selected_pdfs_to_merge = []

    
    

#Split PDF tab
imageeditor_tab = ttk.Frame(notebook)
notebook.add(imageeditor_tab, text=translate("image_editor"))
# Cấu hình imageeditor_tab để nội dung bên trong có thể co giãn
imageeditor_tab.grid_rowconfigure(0, weight=1)
imageeditor_tab.grid_columnconfigure(0, weight=1)

open_images_button = tk.Button(
    imageeditor_tab,
    text=translate("open_images"),
    command=open_file,
    font=("Segoe UI", 14, "bold"),
    bg="#4CAF50",  # Màu nền
    fg="white",  # Màu chữ
    relief="flat",  # Loại bỏ viền nổi
    bd=0,  # Không có border
    cursor="hand2",  # Con trỏ tay khi hover
    activebackground="#45a049",  # Màu khi nhấn
    activeforeground="white",  # Màu chữ khi nhấn
    width=30,  # Chiều rộng cố định
    height=2  # Chiều cao cố định
)
open_images_button.grid(row=0, column=0, pady=20)


# Tạo một Label để hiển thị văn bản
#text_content = translate("image_editor_text_content")

#editor_images_content = tk.Label(imageeditor_tab, text=translate("image_editor_text_content"))


images_content = tk.Label(imageeditor_tab, text=translate("image_editor_text_content"), font=("Segoe UI", 14), justify="center")
images_content.grid(pady=50)  # Thêm Label vào cửa sổ và căn giữa

# Cấu hình grid để notebook chiếm toàn bộ cửa sổ
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)






# 📌 Footer Frame (căn giữa nội dung)
footer_frame = tk.Frame(root, bg="#dddddd")
footer_frame.grid(row=10, column=0, columnspan=4, sticky="we", padx=5, pady=2)
footer_frame.grid_columnconfigure(0, weight=1)  # Căn giữa toàn bộ nội dung

# 📌 Frame con để gộp tất cả nội dung vào giữa
content_frame = tk.Frame(footer_frame, bg="#dddddd")
content_frame.grid(row=0, column=0)  

# 👉 Label chứa "© FreeBird" (click mở About)
copyright_c_label = tk.Label(content_frame, text="©", font=("Segoe UI", 11, "bold"), bg="#dddddd")
copyright_c_label.pack(side="left")

freebird_label = tk.Label(content_frame, text="FreeBird proj", font=("Segoe UI", 10, "bold",),
                          fg="blue", bg="#dddddd", cursor="hand2")
freebird_label.pack(side="left")
freebird_label.bind("<Button-1>", lambda event: show_about_page(notebook))

# 👉 Label chứa ", Email:" (chỉ là văn bản, không phải liên kết)
email_text_label = tk.Label(content_frame, text="| Contact us via email at", font=("Segoe UI", 10, "bold"), bg="#dddddd")
email_text_label.pack(side="left")

# 👉 Label chứa "contact@ngoc.info" (có thể click)
email_label = tk.Label(content_frame, text="contact@ngoc.info", font=("Segoe UI", 10, "bold",),
                       fg="blue", bg="#dddddd", cursor="hand2")
email_label.pack(side="left")
email_label.bind("<Button-1>", open_email)  # Gọi hàm khi click

# 📌 "From Vietnam, with love ❤️" (Đặt ngay bên dưới)
image_path = r"images/heart.png"
img_heart = Image.open(image_path)  
img_heart_resized = img_heart.resize((15, 15)) 
heart_img_resized = ImageTk.PhotoImage(img_heart_resized) 

fromvietnam_label = tk.Label(footer_frame, text="From Vietnam, with love ", font=("Segoe UI", 10, "bold"), 
                             bg="#dddddd", justify="center", compound="right", image=heart_img_resized)
fromvietnam_label.image = heart_img_resized
fromvietnam_label.grid(row=1, column=0, sticky="we", pady=(2, 0))  # Căn giữa




# 📌 Copyright và "Made with love" (Giữ nguyên)
copyright_label = tk.Label(root, text=translate("copyright"), font=("Segoe UI", 10, "bold"), bg="#dddddd")
copyright_label.grid(row=12, column=0, columnspan=4, sticky="we", padx=5, pady=5)

made_with_label = tk.Label(root, text=translate("made_with"), font=("Segoe UI", 10, "bold"), bg="#dddddd")
made_with_label.grid(row=13, column=0, columnspan=4, sticky="we", padx=5, pady=5)






# Đăng ký sự kiện cho tất cả các label
add_interaction(vi_button)
add_interaction(en_button)
add_interaction(zh_button)
add_interaction(es_button)
add_interaction(jp_button)
add_interaction(merge_button)
add_interaction(input_pdfs_button)
add_interaction(output_pdf_button)
add_interaction(previous_page_button)
add_interaction(next_page_button)
add_interaction(extract_text_button)
add_interaction(convert_to_images_button)
add_interaction(convert_to_word_button)
add_interaction(encrypt_button)
add_interaction(split_button)
add_interaction(output_folder_button)
add_interaction(input_pdf_button)
add_interaction(open_images_button)

# Call refresh_ui after notebook is defined
refresh_ui(notebook)

def update_menu_translations():
    """Update menu labels with new translations"""
    # File Menu
    file_menu.entryconfig(0, label=translate("split_pdf"))
    file_menu.entryconfig(1, label=translate("merge_pdf"))
    file_menu.entryconfig(3, label=translate("exit"))
    
    # Settings Menu
    settings_menu.entryconfig(0, label=translate("settings"))
    
    # Edit Menu
    edit_menu.entryconfig(0, label=translate("undo"))
    edit_menu.entryconfig(1, label=translate("clear_all"))
    
    # Help Menu
    help_menu.entryconfig(0, label=translate("about"))
    help_menu.entryconfig(1, label=translate("help_contents"))
    help_menu.entryconfig(2, label=translate("software_update"))

# Hiển thị thông tin tệp ban đầu
root.mainloop()
