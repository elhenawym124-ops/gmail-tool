from nicegui import ui, app
from logic import ChromeAccountManager
import os
from typing import List, Dict

# Initialize logic
manager = ChromeAccountManager()

# --- Design System Constants ---
PRIMARY = '#4f46e5'  # Indigo Modern
SECONDARY = '#0ea5e9' # Ocean Blue
WARNING = '#f59e0b'   # Amber
DARK_BG = '#020617'   # Slate 950 (Very Dark)
CARD_BG = 'rgba(30, 41, 59, 0.6)'  # Semi-transparent Slate 800

def init_styles():
    ui.query('body').style(f'background-color: {DARK_BG}; color: white; font-family: "Outfit", sans-serif;')
    ui.query('.q-page-container').style(f'background-color: {DARK_BG};')
    ui.add_head_html('''
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        
        body::before {
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: radial-gradient(circle at 15% 50%, rgba(79, 70, 229, 0.15), transparent 25%),
                        radial-gradient(circle at 85% 30%, rgba(14, 165, 233, 0.15), transparent 25%);
            z-index: -1;
        }

        .glass-card {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        }
        .stat-card {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .stat-card:hover {
            transform: translateY(-5px) scale(1.02);
            border-color: rgba(79, 70, 229, 0.3);
            box-shadow: 0 10px 40px rgba(79, 70, 229, 0.2);
        }
        .q-table__card {
            background-color: transparent !important;
            box-shadow: none !important;
        }
        .q-table th {
            font-weight: 700 !important;
            color: #94a3b8 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
        }
        .q-table td {
            color: #e2e8f0 !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.02) !important;
        }
        .q-table tbody tr:hover {
            background: rgba(255, 255, 255, 0.02) !important;
        }
        .q-btn {
            border-radius: 8px;
            text-transform: none;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        .q-btn:hover {
            transform: scale(1.05);
        }
        .sidebar-item {
            border-radius: 8px;
            margin: 4px 8px;
            transition: all 0.2s;
        }
        .sidebar-item:hover {
            background: rgba(255, 255, 255, 0.05);
            padding-left: 16px;
        }
        .active-sidebar-item {
            background: linear-gradient(90deg, rgba(79, 70, 229, 0.2) 0%, transparent 100%) !important;
            border-left: 3px solid #4f46e5;
            color: #818cf8 !important;
            font-weight: bold;
        }
    </style>
    ''')

# --- State Management ---
class AppState:
    def __init__(self):
        self.accounts = manager.extract_accounts()
        self.watchlist = manager.watchlist_data
        self.search_query = ''
        self.selected_platform = 'الكل'
        self.filtered_accounts = self.accounts
        self.selected_rows = []

    def refresh(self, silent=False):
        self.accounts = manager.extract_accounts()
        # Prune watchlist automatically
        restored_count = manager.prune_watchlist([a['email'] for a in self.accounts])
        self.watchlist = manager.watchlist_data
        
        self.filter_data()
        try:
            platform_list.refresh()
        except:
            pass
        
        if not silent:
            msg = 'تم تحديث البيانات بنجاح'
            if restored_count > 0:
                msg += f' (تم العثور على {restored_count} إيميل من قائمة المراقبة!)'
            ui.notify(msg, type='positive', color=SECONDARY)

    def filter_data(self):
        if self.selected_platform == 'قائمة المراقبة':
            data = [{"email": e, "profile_name": "Watchlist", "tags": "مفقود", "profile_dir": None} for e in self.watchlist]
        else:
            data = self.accounts
            # Filter by platform sidebar
            if self.selected_platform != 'الكل':
                data = [a for a in data if a['tags'] == self.selected_platform]
        
        # Filter by search
        if self.search_query:
            q = self.search_query.lower()
            data = [
                a for a in data 
                if q in a['email'].lower() or q in a['profile_name'].lower() or q in a['tags'].lower()
            ]
        
        self.filtered_accounts = data
        try:
            table.rows = self.filtered_accounts
        except:
            pass

    def get_platforms(self) -> Dict[str, int]:
        counts = {}
        for a in self.accounts:
            tag = a['tags']
            if tag:
                counts[tag] = counts.get(tag, 0) + 1
        return counts

state = None

# --- Actions ---
def copy_to_clipboard(text):
    ui.run_javascript(f'navigator.clipboard.writeText("{text}")')
    ui.notify(f'تم النسخ بنجاح', color='positive')

def open_chrome(profile_dir, email=None):
    email_label = f" ({email})" if email else ""
    ui.notify(f'جاري تشغيل Chrome (بروفايل: {profile_dir}){email_label}...', color='info')
    manager.launch_chrome(profile_dir, email=email)

def open_edit_dialog(row=None, selection=None):
    if selection:
        emails = [r['email'] for r in selection]
        title = f'تعديل المنصات لـ {len(emails)} حساب'
        current_tags = ""
    else:
        emails = [row['email']]
        title = f'تعديل المنصات لـ {row["email"]}'
        current_tags = row['tags']
    
    with ui.dialog() as dialog, ui.card().classes('w-96 glass-card p-6'):
        ui.label(title).classes('text-lg font-bold mb-4')
        tag_input = ui.input('المنصات (فواصل بين الكلمات)', value=current_tags).classes('w-full mb-6').props('dark standout')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('إلغاء', on_click=dialog.close).props('flat')
            def save():
                for email in emails:
                    manager.update_tag(email, tag_input.value)
                state.refresh(silent=True)
                dialog.close()
            ui.button('حفظ', on_click=save).props('color=primary')
    dialog.open()

def open_credential_dialog(row):
    title = f'بيانات الدخول لـ {row["email"]}'
    with ui.dialog() as dialog, ui.card().classes('w-96 glass-card p-6'):
        ui.label(title).classes('text-lg font-bold mb-4')
        pwd_input = ui.input('كلمة السر (Password)', value=row.get('password', '')).classes('w-full mb-4').props('dark standout password-toggle')
        recovery_input = ui.input('إيميل الاسترداد (Recovery Email)', value=row.get('recovery_email', '')).classes('w-full mb-6').props('dark standout')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('إلغاء', on_click=dialog.close).props('flat')
            def save():
                manager.update_credentials(row['email'], pwd_input.value, recovery_input.value)
                state.refresh(silent=True)
                dialog.close()
            ui.button('حفظ', on_click=save).props('color=primary')
    dialog.open()

def run_login_assistant(profile_dir, email):
    creds = manager.get_credentials(email)
    pwd = creds.get('password')
    recovery = creds.get('recovery_email')
    
    if not pwd:
        ui.notify('من فضلك أضف كلمة السر أولاً من أيقونة المفتاح', type='warning')
        return
    
    login_url = f"https://accounts.google.com/ServiceLogin?Email={email}&continue=https://mail.google.com/mail/"
    manager.launch_chrome(profile_dir, email=email, url=login_url)
    copy_to_clipboard(pwd)
    ui.notify(f'تم تشغيل المساعد. قم بلصق كلمة السر (في الذاكرة الآن).', type='info', duration=10)
    if recovery:
        ui.notify(f'إيميل الاسترداد: {recovery}', type='info', duration=10)

def open_bulk_credentials_dialog():
    with ui.dialog() as dialog, ui.card().classes('w-[600px] glass-card p-6'):
        ui.label('استيراد بيانات الدخول (Bulk Import)').classes('text-xl font-bold mb-2')
        ui.label('الصيغة: email:password أو email:password:recovery').classes('text-sm text-slate-400 mb-4')
        
        area = ui.textarea('لصق القائمة هنا (سطر لكل حساب)').classes('w-full h-64 mb-6').props('dark standout')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('إلغاء', on_click=dialog.close).props('flat')
            
            def process():
                text = area.value.strip()
                if not text:
                    ui.notify('من فضلك أدخل بيانات أولاً', type='warning')
                    return
                
                lines = text.split('\n')
                parsed_list = []
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    parts = []
                    for sep in ['|', ':', ',', '\t']:
                        if sep in line:
                            parts = [p.strip() for p in line.split(sep)]
                            break
                    if not parts:
                        parts = line.split()
                        
                    if len(parts) >= 2:
                        parsed_list.append({
                            "email": parts[0],
                            "password": parts[1],
                            "recovery_email": parts[2] if len(parts) > 2 else ""
                        })
                
                if parsed_list:
                    manager.bulk_update_credentials(parsed_list)
                    ui.notify(f'تم استيراد {len(parsed_list)} حساب بنجاح!', type='positive')
                    state.refresh(silent=True)
                    dialog.close()
                else:
                    ui.notify('لم يتم العثور على بيانات صالحة. تحقق من الصيغة.', type='negative')
            
            ui.button('استيراد الآن', on_click=process).props('color=primary icon=cloud_upload')
    dialog.open()

def download_csv():
    csv_data = manager.export_to_csv(state.filtered_accounts)
    ui.download(csv_data.encode(), filename="gmail_accounts_export.csv")
    ui.notify("تم تصدير البيانات بنجاح", color=SECONDARY)

def bulk_copy_emails():
    emails = "\n".join([r['email'] for r in state.selected_rows])
    copy_to_clipboard(emails)
    ui.notify(f"تم نسخ {len(state.selected_rows)} إيميل", color=PRIMARY)

def cleanup_orphaned_tags():
    active_emails = [a['email'] for a in state.accounts]
    removed = manager.cleanup_tags(active_emails)
    ui.notify(f"تم تنظيف {removed} وسم قديم", color=WARNING)
    state.refresh()

def delete_from_watchlist(email):
    if manager.remove_from_watchlist(email):
        ui.notify('تم الحذف من قائمة المراقبة', color='info')
        state.refresh(silent=True)

def show_results(found, missing):
    with ui.dialog() as result_dialog, ui.card().classes('w-[600px] glass-card p-6'):
        ui.label('نتائج الفحص').classes('text-xl font-bold mb-6')
        with ui.row().classes('w-full gap-4'):
            with ui.column().classes('flex-1'):
                ui.label(f'✅ موجود ({len(found)})').classes('text-emerald-400 font-bold mb-2')
                with ui.scroll_area().classes('h-64 border border-slate-800 rounded p-2'):
                    for e in found:
                        ui.label(e).classes('text-xs text-slate-300 border-b border-slate-800 pb-1')
            with ui.column().classes('flex-1'):
                ui.label(f'❌ غير موجود ({len(missing)})').classes('text-rose-400 font-bold mb-2')
                with ui.scroll_area().classes('h-64 border border-slate-800 rounded p-2'):
                    for e in missing:
                        ui.label(e).classes('text-xs text-slate-300 border-b border-slate-800 pb-1')
        with ui.row().classes('w-full gap-2 mt-6'):
            def add_missing_to_watch():
                added = manager.add_to_watchlist(missing)
                ui.notify(f'تم إضافة {added} إيميل لقائمة المراقبة', color=SECONDARY)
                state.refresh(silent=True)
                result_dialog.close()
            ui.button('إضافة المفقودة للمراقبة', icon='visibility', on_click=add_missing_to_watch).props('outline color=warning').classes('flex-1')
            ui.button('إغلاق', on_click=result_dialog.close).classes('flex-1').props('color=primary')
    result_dialog.open()

def show_platform_results(platform_name, matched, unmatched):
    with ui.dialog() as pr_dialog, ui.card().classes('w-[700px] glass-card p-6'):
        ui.label(f'نتائج مطابقة: {platform_name}').classes('text-xl font-bold mb-2')
        with ui.row().classes('w-full gap-4 mb-6'):
            with ui.card().classes('flex-1 p-4 bg-emerald-900/30 rounded-xl border border-emerald-800'):
                ui.label('مسجل بالفعل ✅').classes('text-sm text-emerald-400')
                ui.label(str(len(matched))).classes('text-3xl font-bold text-emerald-300')
            with ui.card().classes('flex-1 p-4 bg-amber-900/30 rounded-xl border border-amber-800'):
                ui.label('لسه مش مضاف ⏳').classes('text-sm text-amber-400')
                ui.label(str(len(unmatched))).classes('text-3xl font-bold text-amber-300')
        with ui.row().classes('w-full gap-4'):
            with ui.column().classes('flex-1'):
                ui.label(f'✅ مسجل على {platform_name}').classes('text-emerald-400 font-bold mb-2 text-sm')
                with ui.scroll_area().classes('h-64 border border-slate-800 rounded p-2 bg-slate-900/50'):
                    for acc in matched:
                        with ui.row().classes('items-center gap-2 w-full border-b border-slate-800 pb-1'):
                            ui.label(acc['email']).classes('text-xs text-slate-300 flex-1')
                            ui.badge(acc['profile_name'], color='slate-700').props('rounded dense')
            with ui.column().classes('flex-1'):
                ui.label(f'⏳ لسه مش على {platform_name}').classes('text-amber-400 font-bold mb-2 text-sm')
                with ui.scroll_area().classes('h-64 border border-slate-800 rounded p-2 bg-slate-900/50'):
                    for acc in unmatched:
                        with ui.row().classes('items-center gap-2 w-full border-b border-slate-800 pb-1'):
                            ui.label(acc['email']).classes('text-xs text-slate-300 flex-1')
                            ui.badge(acc['profile_name'], color='slate-700').props('rounded dense')
        with ui.row().classes('w-full gap-2 mt-6'):
            def copy_unmatched():
                emails_text = '\n'.join([a['email'] for a in unmatched])
                ui.run_javascript(f'navigator.clipboard.writeText(`{emails_text}`)')
                ui.notify(f'تم نسخ {len(unmatched)} إيميل', color='positive')
            if unmatched:
                ui.button(f'نسخ {len(unmatched)} إيميل', icon='content_copy', on_click=copy_unmatched).props('color=warning').classes('flex-1')
            ui.button('إغلاق', on_click=pr_dialog.close).classes('flex-1').props('color=primary')
    pr_dialog.open()

# --- UI Setup ---
@ui.page('/')
def main_page():
    global state, drawer, platform_list, table, bulk_check_dialog, platform_match_dialog
    
    if state is None:
        state = AppState()

    init_styles()

    # Sidebar
    with ui.left_drawer(value=True).classes('bg-slate-900 border-r border-slate-800 p-0') as drawer:
        with ui.column().classes('w-full p-4 gap-2'):
            ui.label('جولة المنصات').classes('text-xs font-bold text-slate-500 uppercase tracking-widest px-2 mb-2')
            
            @ui.refreshable
            def platform_list():
                with ui.column().classes('w-full gap-1'):
                    is_active = state.selected_platform == 'الكل'
                    with ui.row().classes(f'sidebar-item w-full items-center justify-between px-3 py-2 cursor-pointer {"active-sidebar-item" if is_active else ""}') \
                        .on('click', lambda: select_platform('الكل')):
                        ui.label('الكل').classes('text-sm')
                        ui.badge(len(state.accounts), color='slate-700').props('rounded')
                    
                    platforms = state.get_platforms()
                    for p, count in sorted(platforms.items(), key=lambda x: x[1], reverse=True):
                        is_p_active = state.selected_platform == p
                        with ui.row().classes(f'sidebar-item w-full items-center justify-between px-3 py-2 cursor-pointer {"active-sidebar-item" if is_p_active else ""}') \
                            .on('click', lambda p=p: select_platform(p)):
                            ui.label(p).classes('text-sm truncate max-w-[150px]')
                            ui.badge(count, color='primary').props('rounded')
                    
                    ui.separator().classes('my-2 opacity-10')
                    ui.label('التتبع').classes('text-xs font-bold text-slate-500 uppercase tracking-widest px-2 mb-2')
                    is_watch_active = state.selected_platform == 'قائمة المراقبة'
                    with ui.row().classes(f'sidebar-item w-full items-center justify-between px-3 py-2 cursor-pointer {"active-sidebar-item" if is_watch_active else ""}') \
                        .on('click', lambda: select_platform('قائمة المراقبة')):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('visibility', size='xs')
                            ui.label('قائمة المراقبة').classes('text-sm')
                        ui.badge(len(state.watchlist), color='warning').props('rounded')
            
            platform_list()

        with ui.column().classes('absolute-bottom w-full p-4 border-t border-slate-800'):
            ui.button('تنظيف الوسوم', icon='cleaning_services', on_click=cleanup_orphaned_tags) \
                .props('flat color=slate-400 no-caps').classes('w-full justify-start')

    def select_platform(p):
        state.selected_platform = p
        state.filter_data()
        platform_list.refresh()

    # Header
    with ui.header().classes('bg-slate-900/80 backdrop-blur-md border-b border-slate-800 py-4 px-6 items-center justify-between'):
        with ui.row().classes('items-center gap-3'):
            ui.button(on_click=lambda: drawer.toggle(), icon='menu').props('flat round color=white')
            ui.icon('mark_email_unread', color='primary').classes('text-3xl drop-shadow-lg')
            ui.label('Gmail Extractor Pro').classes('text-2xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-sky-400')
        with ui.row().classes('items-center gap-4'):
            ui.button(icon='refresh', on_click=state.refresh).props('flat round color=white')
            ui.button('GitHub', icon='code', on_click=lambda: ui.navigate.to('https://github.com', new_tab=True)).props('outline color=primary')

    with ui.column().classes('w-full max-w-7xl mx-auto p-6 gap-8'):
        with ui.row().classes('w-full gap-6 justify-between'):
            def stat_box(title, value, icon, color):
                with ui.card().classes('glass-card stat-card flex-1 p-4'):
                    with ui.row().classes('items-center justify-between'):
                        with ui.column():
                            ui.label(title).classes('text-sm text-slate-400')
                            ui.label(value).classes('text-3xl font-bold mt-1')
                        ui.icon(icon, color=color).classes('text-4xl opacity-50')
            stat_box('إجمالي الحسابات', len(state.accounts), 'people', 'primary')
            stat_box('بروفايلات Chrome', len(set(a['profile_dir'] for a in state.accounts)), 'browser', 'secondary')
            stat_box('المنصات المسجلة', len(state.get_platforms()), 'sell', 'warning')

        with ui.card().classes('glass-card w-full p-0 overflow-hidden'):
            with ui.row().classes('w-full p-6 items-center justify-between gap-4 border-b border-slate-800'):
                with ui.row().classes('items-center gap-4 flex-1'):
                    ui.input(placeholder='ابحث عن إيميل أو منصة...', on_change=state.filter_data).classes('w-full max-w-sm').props('dark standout rounded dense').bind_value(state, 'search_query')
                with ui.row().classes('gap-2'):
                    ui.button('تصدير CSV', icon='download', on_click=download_csv).props('outline color=primary')
                    ui.button('استيراد بيانات', icon='cloud_upload', on_click=open_bulk_credentials_dialog).props('outline color=secondary')
                    ui.button('فحص لستة إيميلات', icon='checklist', on_click=lambda: bulk_check_dialog.open()).props('color=secondary elevated')
                    ui.button('مطابقة منصة', icon='compare_arrows', on_click=lambda: platform_match_dialog.open()).props('color=warning elevated')

            with ui.row().classes('w-full px-6 py-2 bg-blue-900/20 items-center justify-between transition-all').bind_visibility_from(state, 'selected_rows', backward=lambda s: len(s) > 0):
                ui.label().bind_text_from(state, 'selected_rows', backward=lambda s: f'تم اختيار {len(s)} حساب').classes('text-blue-400 font-bold')
                with ui.row().classes('gap-2'):
                    ui.button('نسخ المحددة', icon='content_copy', on_click=bulk_copy_emails).props('flat dense color=blue-400')
                    ui.button('وسم المحددة', icon='sell', on_click=lambda: open_edit_dialog(selection=state.selected_rows)).props('flat dense color=blue-400')

            columns = [
                {'name': 'profile_name', 'label': 'البروفايل', 'field': 'profile_name', 'align': 'left', 'sortable': True},
                {'name': 'email', 'label': 'Gmail / الإيميل', 'field': 'email', 'align': 'left', 'sortable': True},
                {'name': 'tags', 'label': 'المنصات', 'field': 'tags', 'align': 'left', 'sortable': True},
                {'name': 'actions', 'label': 'إجراءات', 'field': 'id', 'align': 'right'},
            ]
            table = ui.table(columns=columns, rows=state.filtered_accounts, row_key='email', selection='multiple', on_select=lambda e: setattr(state, 'selected_rows', e.selection)).classes('w-full bg-transparent')
            
            table.add_slot('body-cell-tags', '''<q-td :props="props"><q-badge v-if="props.value" color="primary" outline rounded>{{ props.value }}</q-badge><span v-else class="text-slate-500 italic text-xs">لا يوجد</span></q-td>''')
            table.add_slot('body-cell-actions', '''<q-td :props="props">
                <q-btn flat round color="primary" icon="content_copy" size="sm" @click="$parent.$emit('copy', props.row.email)"><q-tooltip>نسخ الإيميل</q-tooltip></q-btn>
                <q-btn v-if="props.row.profile_dir" flat round color="secondary" icon="open_in_new" size="sm" @click="$parent.$emit('launch', {profile_dir: props.row.profile_dir, email: props.row.email})"><q-tooltip>فتح في Chrome</q-tooltip></q-btn>
                <q-btn v-if="props.row.profile_dir" flat round color="primary" icon="vpn_key" size="sm" @click="$parent.$emit('creds', props.row)"><q-tooltip>بيانات الدخول</q-tooltip></q-btn>
                <q-btn v-if="props.row.profile_dir" flat round color="warning" icon="auto_fix_high" size="sm" @click="$parent.$emit('login_assist', {profile_dir: props.row.profile_dir, email: props.row.email})"><q-tooltip>مساعد تسجيل الدخول</q-tooltip></q-btn>
                <q-btn v-if="props.row.profile_dir" flat round color="amber" icon="edit" size="sm" @click="$parent.$emit('edit', props.row)"><q-tooltip>تعديل المنصات</q-tooltip></q-btn>
                <q-btn v-else flat round color="negative" icon="delete" size="sm" @click="$parent.$emit('delete_watch', props.row.email)"><q-tooltip>حذف من المراقبة</q-tooltip></q-btn>
            </q-td>''')

            table.on('copy', lambda msg: copy_to_clipboard(msg.args))
            table.on('launch', lambda msg: open_chrome(msg.args['profile_dir'], msg.args['email']))
            table.on('creds', lambda msg: open_credential_dialog(msg.args))
            table.on('login_assist', lambda msg: run_login_assistant(msg.args['profile_dir'], msg.args['email']))
            table.on('edit', lambda msg: open_edit_dialog(row=msg.args))
            table.on('delete_watch', lambda msg: delete_from_watchlist(msg.args))

    # Dialogs defined inside main_page to have access to context if needed
    with ui.dialog() as bulk_check_dialog, ui.card().classes('w-[500px] glass-card p-6'):
        ui.label('فحص مجموعة إيميلات').classes('text-xl font-bold mb-2')
        bulk_input = ui.textarea().classes('w-full h-64 mb-4').props('dark standout filled')
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('إلغاء', on_click=bulk_check_dialog.close).props('flat')
            def run_bulk_check():
                lines = bulk_input.value.strip().split('\n')
                input_emails = [l.strip().lower() for l in lines if l.strip()]
                existing_emails = {a['email'].lower() for a in state.accounts}
                found = [e for e in input_emails if e in existing_emails]
                missing = [e for e in input_emails if e not in existing_emails]
                bulk_check_dialog.close()
                show_results(found, missing)
            ui.button('بدء الفحص', on_click=run_bulk_check).props('color=secondary')

    with ui.dialog() as platform_match_dialog, ui.card().classes('w-[550px] glass-card p-6'):
        ui.label('مطابقة منصة').classes('text-xl font-bold mb-1')
        platform_name_input = ui.input('اسم المنصة').classes('w-full mb-4').props('dark standout')
        platform_emails_input = ui.textarea().classes('w-full h-48 mb-4').props('dark standout filled')
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('إلغاء', on_click=platform_match_dialog.close).props('flat')
            def run_platform_match():
                p_name = platform_name_input.value.strip()
                lines = platform_emails_input.value.strip().split('\n')
                platform_emails = {l.strip().lower() for l in lines if l.strip()}
                if not p_name or not platform_emails:
                    ui.notify('بيانات ناقصة', type='warning')
                    return
                already_on_platform = [a for a in state.accounts if a['email'].lower() in platform_emails]
                not_on_platform = [a for a in state.accounts if a['email'].lower() not in platform_emails]
                for acc in already_on_platform:
                    existing_tag = acc['tags']
                    if existing_tag and p_name not in existing_tag:
                        manager.update_tag(acc['email'], f"{existing_tag}, {p_name}")
                    elif not existing_tag:
                        manager.update_tag(acc['email'], p_name)
                platform_match_dialog.close()
                state.refresh(silent=True)
                show_platform_results(p_name, already_on_platform, not_on_platform)
            ui.button('بدء المطابقة', icon='compare_arrows', on_click=run_platform_match).props('color=warning')

if __name__ == '__main__':
    import multiprocessing
    import sys
    import traceback
    multiprocessing.freeze_support()
    try:
        ui.run(title='Gmail Extractor Pro', favicon='📧', native=False, window_size=(1400, 900), reload=False, dark=True)
    except Exception as e:
        with open('crash_log.txt', 'w', encoding='utf-8') as f:
            f.write(traceback.format_exc())
        raise e
