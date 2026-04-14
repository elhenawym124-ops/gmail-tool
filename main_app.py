from nicegui import ui, app
from logic import ChromeAccountManager
import os

# Initialize logic
manager = ChromeAccountManager()

# --- Design System Constants ---
PRIMARY = '#3b82f6'  # Modern Blue
SECONDARY = '#10b981' # Emerald Green
DARK_BG = '#0f172a'   # Deep Blue Slate
CARD_BG = '#1e293b'   # Lighter Slate for cards

# Configure App
ui.query('body').style(f'background-color: {DARK_BG}; color: white; font-family: "Outfit", sans-serif;')
ui.query('.q-page-container').style(f'background-color: {DARK_BG};')

def set_style():
    ui.add_head_html('''
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        .glass-card {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
        }
        .stat-card {
            transition: transform 0.2s ease-in-out;
        }
        .stat-card:hover {
            transform: translateY(-5px);
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
        }
        .q-table td {
            color: #e2e8f0 !important;
        }
        .q-btn {
            border-radius: 8px;
            text-transform: none;
            font-weight: 600;
        }
    </style>
    ''')

# --- State Management ---
class AppState:
    def __init__(self):
        self.accounts = manager.extract_accounts()
        self.search_query = ''
        self.filtered_accounts = self.accounts

    def refresh(self):
        self.accounts = manager.extract_accounts()
        self.filter_data()
        ui.notify('تم تحديث البيانات بنجاح', type='positive', color=SECONDARY)

    def filter_data(self):
        if not self.search_query:
            self.filtered_accounts = self.accounts
        else:
            q = self.search_query.lower()
            self.filtered_accounts = [
                a for a in self.accounts 
                if q in a['email'].lower() or q in a['profile_name'].lower() or q in a['tags'].lower()
            ]
        table.rows = self.filtered_accounts

state = AppState()

# --- UI Components ---

@ui.page('/')
def main_page():
    set_style()
    
    with ui.header().classes('bg-slate-900 border-b border-slate-800 py-4 px-6 items-center justify-between'):
        with ui.row().classes('items-center gap-3'):
            ui.icon('alternate_email', color='primary').classes('text-3xl')
            ui.label('Gmail Extractor Pro').classes('text-2xl font-bold tracking-tight')
        
        with ui.row().classes('items-center gap-4'):
            ui.button(icon='refresh', on_click=state.refresh).props('flat round color=white')
            ui.button('GitHub', icon='code', on_click=lambda: ui.open('https://github.com')).props('outline color=primary')

    with ui.column().classes('w-full max-w-7xl mx-auto p-6 gap-8'):
        
        # --- Stats Bar ---
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
            stat_box('المنصات المسجلة', len(set(a['tags'] for a in state.accounts if a['tags'])), 'sell', 'warning')

        # --- Main Table Section ---
        with ui.card().classes('glass-card w-full p-0 overflow-hidden'):
            with ui.row().classes('w-full p-6 items-center justify-between gap-4 border-b border-slate-800'):
                with ui.row().classes('items-center gap-4 flex-1'):
                    ui.input(placeholder='ابحث عن إيميل أو منصة...', 
                             on_change=state.filter_data).classes('w-full max-w-sm') \
                             .props('dark standout rounded dense') \
                             .bind_value(state, 'search_query')
                
                ui.button('فحص لستة إيميلات', icon='checklist', on_click=lambda: bulk_check_dialog.open()) \
                    .props('color=secondary elevated')

            global table
            columns = [
                {'name': 'profile_name', 'label': 'البروفايل', 'field': 'profile_name', 'align': 'left', 'sortable': True},
                {'name': 'email', 'label': 'Gmail / الإيميل', 'field': 'email', 'align': 'left', 'sortable': True},
                {'name': 'tags', 'label': 'المنصات', 'field': 'tags', 'align': 'left', 'sortable': True},
                {'name': 'actions', 'label': 'إجراءات', 'field': 'id', 'align': 'right'},
            ]
            
            table = ui.table(columns=columns, rows=state.filtered_accounts, row_key='email').classes('w-full')
            
            # Custom slot for tags and actions
            table.add_slot('body-cell-tags', '''
                <q-td :props="props">
                    <q-badge v-if="props.value" color="primary" outline rounded>
                        {{ props.value }}
                    </q-badge>
                    <span v-else class="text-slate-500 italic text-xs">لا يوجد</span>
                </q-td>
            ''')
            
            table.add_slot('body-cell-actions', '''
                <q-td :props="props">
                    <q-btn flat round color="primary" icon="content_copy" size="sm" @click="$parent.$emit('copy', props.row.email)">
                        <q-tooltip>نسخ الإيميل</q-tooltip>
                    </q-btn>
                    <q-btn flat round color="secondary" icon="open_in_new" size="sm" @click="$parent.$emit('launch', props.row.profile_dir)">
                        <q-tooltip>فتح في Chrome</q-tooltip>
                    </q-btn>
                    <q-btn flat round color="warning" icon="edit" size="sm" @click="$parent.$emit('edit', props.row)">
                        <q-tooltip>تعديل المنصات</q-tooltip>
                    </q-btn>
                </q-td>
            ''')

            table.on('copy', lambda msg: copy_to_clipboard(msg.args))
            table.on('launch', lambda msg: open_chrome(msg.args))
            table.on('edit', lambda msg: open_edit_dialog(msg.args))

# --- Actions ---

def copy_to_clipboard(email):
    ui.run_javascript(f'navigator.clipboard.writeText("{email}")')
    ui.notify(f'تم نسخ {email}', color='positive')

def open_chrome(profile_dir):
    ui.notify(f'جاري تشغيل Chrome (بروفايل: {profile_dir})...', color='info')
    manager.launch_chrome(profile_dir)

def open_edit_dialog(row):
    email = row['email']
    current_tags = row['tags']
    
    with ui.dialog() as dialog, ui.card().classes('w-96 glass-card p-6'):
        ui.label(f'تعديل المنصات لـ {email}').classes('text-lg font-bold mb-4')
        tags_input = ui.input('المنصات (ChatGPT, Gemini...)', value=current_tags).classes('w-full mb-6').props('dark standout')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('إلغاء', on_click=dialog.close).props('flat')
            def save():
                manager.update_tag(email, tags_input.value)
                state.refresh()
                dialog.close()
            ui.button('حفظ', on_click=save).props('color=primary')
    dialog.open()

# --- Bulk Check Dialog ---
with ui.dialog() as bulk_check_dialog, ui.card().classes('w-[500px] glass-card p-6'):
    ui.label('فحص مجموعة إيميلات').classes('text-xl font-bold mb-2')
    ui.label('الصق الإيميلات هنا (واحد في كل سطر)').classes('text-sm text-slate-400 mb-4')
    
    bulk_input = ui.textarea().classes('w-full h-64 mb-4').props('dark standout filled')
    
    with ui.row().classes('w-full justify-end gap-2'):
        ui.button('إغاء', on_click=bulk_check_dialog.close).props('flat')
        
        def run_bulk_check():
            lines = bulk_input.value.strip().split('\\n')
            input_emails = [l.strip().lower() for l in lines if l.strip()]
            existing_emails = {a['email'].lower() for a in state.accounts}
            
            found = [e for e in input_emails if e in existing_emails]
            missing = [e for e in input_emails if e not in existing_emails]
            
            bulk_check_dialog.close()
            show_results(found, missing)
            
        ui.button('بدء الفحص', on_click=run_bulk_check).props('color=secondary')

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
        
        ui.button('إغلاق', on_click=result_dialog.close).classes('mt-6 w-full').props('outline color=white')
    result_dialog.open()

# Run the app
ui.run(title='Gmail Extractor Pro', port=8080, reload=True, favicon='📧')
