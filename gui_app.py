import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess

TAGS_FILE = os.path.join(os.path.dirname(__file__), "gmail_tags.json")

def load_tags():
    if os.path.exists(TAGS_FILE):
        try:
            with open(TAGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_tags(tags):
    try:
        with open(TAGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tags, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Error saving tags:", e)

def extract_emails():
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    if not local_app_data:
        return {"error": "LOCALAPPDATA environment variable not found."}

    user_data_path = os.path.join(local_app_data, 'Google', 'Chrome', 'User Data')
    
    if not os.path.exists(user_data_path):
        return {"error": f"Chrome User Data not found at: {user_data_path}"}

    try:
        all_dirs = [d for d in os.listdir(user_data_path) if os.path.isdir(os.path.join(user_data_path, d))]
    except PermissionError:
        return {"error": "Permission denied. Ensure Chrome is closed."}

    profiles = [d for d in all_dirs if d == 'Default' or d.startswith('Profile ')]
    results = []
    
    for p in sorted(profiles):
        pref_path = os.path.join(user_data_path, p, 'Preferences')
        if not os.path.exists(pref_path):
            continue
            
        try:
            with open(pref_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            emails = set()
            name = "Unknown Profile"
            
            if 'profile' in data and 'name' in data['profile']:
                name = data['profile']['name']
                
            for acc in data.get('account_info', []):
                email = acc.get('email', '')
                if email:
                    emails.add(email)
            
            signin_email = data.get('google', {}).get('services', {}).get('signin', {}).get('email')
            if signin_email:
                emails.add(signin_email)
                
            for em in emails:
                results.append((p, name, em))
                
        except Exception:
            pass
            
    return results

class GmailExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chrome Gmail Extractor")
        self.root.geometry("850x550")
        self.root.configure(padx=10, pady=10)

        self.tags_data = load_tags()
        self.all_data = []

        # Header
        self.header_label = ttk.Label(self.root, text="حسابات Gmail في بروفايلات Chrome", font=("Arial", 16, "bold"))
        self.header_label.pack(pady=(0, 5))
        
        self.hint_label = ttk.Label(self.root, text="💡 اضغط مرتين (Double Click) لفتح Gmail، أو كليك يمين للنسخ وتعديل المنصات.", foreground="gray")
        self.hint_label.pack(pady=(0, 10))

        # Action Frame (Search & Extract)
        action_frame = ttk.Frame(self.root)
        action_frame.pack(fill=tk.X, pady=5)

        self.extract_btn = ttk.Button(action_frame, text="🔁 تحديث وتحديث الحسابات", command=self.load_data)
        self.extract_btn.pack(side=tk.RIGHT, padx=5)
        
        self.compare_btn = ttk.Button(action_frame, text="📑 فحص لستة إيميلات", command=self.open_compare_window)
        self.compare_btn.pack(side=tk.RIGHT, padx=5)

        ttk.Label(action_frame, text="🔍 بحث (إيميل/منصة):").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_data)
        self.search_entry = ttk.Entry(action_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)

        # Status
        self.status_var = tk.StringVar(value="جاهز.")
        self.status_label = ttk.Label(self.root, textvariable=self.status_var, foreground="blue")
        self.status_label.pack(pady=5)

        # Table
        columns = ("profile", "name", "email", "tags")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=15)
        
        self.tree.heading("profile", text="Profile Directory")
        self.tree.heading("name", text="Profile Name")
        self.tree.heading("email", text="Gmail Account")
        self.tree.heading("tags", text="المنصات / ملاحظات")
        
        self.tree.column("profile", width=110, anchor=tk.CENTER)
        self.tree.column("name", width=140, anchor=tk.CENTER)
        self.tree.column("email", width=250, anchor=tk.W)
        self.tree.column("tags", width=180, anchor=tk.W)

        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Right Click Menu
        self.menu = tk.Menu(self.root, tearoff=0, font=("Arial", 10))
        self.menu.add_command(label="📋 نسخ الإيميل", command=self.copy_email)
        self.menu.add_command(label="🌐 فتح في Gmail", command=self.open_gmail)
        self.menu.add_separator()
        self.menu.add_command(label="🏷️ إضافة/تعديل المنصات", command=self.edit_tags)

        # Bindings
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#f0f0f0")
        style.configure("Treeview", font=("Arial", 10), rowheight=25)
        
        # Load automatically
        self.load_data()

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.menu.tk_popup(event.x_root, event.y_root)

    def on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.open_gmail()

    def get_selected_data(self):
        selected_item = self.tree.selection()
        if selected_item:
            return self.tree.item(selected_item[0])['values'], selected_item[0]
        return None, None

    def copy_email(self):
        data, _ = self.get_selected_data()
        if data:
            email = data[2]
            self.root.clipboard_clear()
            self.root.clipboard_append(email)
            self.status_var.set(f"تم نسخ '{email}' إلى الحافظة بنجاح ✅")

    def edit_tags(self):
        data, item_id = self.get_selected_data()
        if data:
            email = data[2]
            current_tags = data[3] if len(data) > 3 else ""
            
            new_tags = simpledialog.askstring(
                "تعديل المنصات", 
                f"أدخل المنصات الخاصة بـ {email}\n(مثال: ChatGPT, Gemini, Facebook):",
                initialvalue=current_tags,
                parent=self.root
            )
            
            if new_tags is not None:
                new_tags = new_tags.strip()
                self.tags_data[email] = new_tags
                save_tags(self.tags_data)
                
                updated_values = (data[0], data[1], data[2], new_tags)
                self.tree.item(item_id, values=updated_values)
                
                for i, row in enumerate(self.all_data):
                    if row[2] == email:
                        self.all_data[i] = updated_values
                        break
                        
                self.status_var.set(f"تم حفظ المنصات للإيميل {email}")

    def open_gmail(self):
        data, _ = self.get_selected_data()
        if data:
            profile_dir = data[0]
            email = data[2]
            try:
                cmd = f'start chrome --profile-directory="{profile_dir}" "https://mail.google.com/mail/u/0/"'
                subprocess.Popen(cmd, shell=True)
                self.status_var.set(f"جاري تشغيل Chrome وفتح البريد {email} ... 🌐")
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء محاولة تشغيل المتصفح:\n{str(e)}")

    def filter_data(self, *args):
        query = self.search_var.get().lower()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        count = 0
        for row in self.all_data:
            row_str = " ".join(str(v).lower() for v in row)
            if query in row_str:
                self.tree.insert("", tk.END, values=row)
                count += 1
                
        if query:
            self.status_var.set(f"نتيجة البحث: {count} حساب(ات)")
        else:
            self.status_var.set(f"تم إيجاد {len(self.all_data)} حساب بنجاح!")

    def load_data(self):
        self.status_var.set("جاري البحث والاستخراج...")
        self.root.update_idletasks()
        
        raw_results = extract_emails()
        
        if isinstance(raw_results, dict) and "error" in raw_results:
            messagebox.showerror("خطأ", raw_results["error"])
            self.status_var.set("حدث خطأ أثناء الاستخراج.")
            return

        self.all_data = []
        for p, name, em in raw_results:
            tag = self.tags_data.get(em, "")
            self.all_data.append((p, name, em, tag))

        self.filter_data()

    def open_compare_window(self):
        comp_win = tk.Toplevel(self.root)
        comp_win.title("مقارنة لستة إيميلات")
        comp_win.geometry("500x450")
        comp_win.configure(padx=10, pady=10)
        
        ttk.Label(comp_win, text="الصق لستة الإيميلات هنا (إيميل في كل سطر):", font=("Arial", 11, "bold")).pack(pady=(0, 5))
        
        text_area = tk.Text(comp_win, height=15, width=55, font=("Arial", 10))
        text_area.pack(pady=5, fill=tk.BOTH, expand=True)
        
        def run_compare():
            content = text_area.get("1.0", tk.END).strip()
            if not content:
                messagebox.showwarning("تنبيه", "يرجى لصق الإيميلات أولاً!", parent=comp_win)
                return
                
            emails = content.splitlines()
            emails = [e.strip().lower() for e in emails if e.strip()]
            
            existing_emails = {str(row[2]).lower() for row in self.all_data}
            
            found = []
            missing = []
            
            for e in set(emails): # Handle duplicates in input gracefully
                if e in existing_emails:
                    found.append(e)
                else:
                    missing.append(e)
                    
            res_win = tk.Toplevel(comp_win)
            res_win.title("نتيجة الفحص")
            res_win.geometry("450x400")
            res_win.configure(padx=10, pady=10)
            
            # Simple scrolling text view for results
            res_text = tk.Text(res_win, font=("Arial", 12), state=tk.NORMAL)
            res_text.pack(fill=tk.BOTH, expand=True)
            
            res_text.insert(tk.END, f"✅ الإيميلات الموجودة في الجهاز ({len(found)}):\n------------------------------------\n", "found_head")
            for f in found:
                res_text.insert(tk.END, f"{f}\n", "found")
                
            res_text.insert(tk.END, f"\n❌ الإيميلات غير الموجودة ({len(missing)}):\n------------------------------------\n", "miss_head")
            for m in missing:
                res_text.insert(tk.END, f"{m}\n", "miss")
                
            res_text.tag_config("found_head", foreground="green", font=("Arial", 12, "bold"))
            res_text.tag_config("miss_head", foreground="red", font=("Arial", 12, "bold"))
            res_text.tag_config("found", foreground="darkgreen")
            res_text.tag_config("miss", foreground="darkred")
            res_text.configure(state=tk.DISABLED) # Read only
                
        ttk.Button(comp_win, text="بدء المقارنة الفحص", command=run_compare).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = GmailExtractorApp(root)
    root.mainloop()
