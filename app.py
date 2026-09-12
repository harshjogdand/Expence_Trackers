import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
import json
import os

# ============================================================
# EXPENSEFLOW PRO - PERSONAL FINANCE MANAGER
# Final combined build: Salary/Transaction/Goal Edit + Delete + Emergency Fund
# ============================================================

DATA_FILE = "expenseflow_data.json"

THEMES = {
    "Midnight Purple": {
        "bg": "#F4F2FF", "card": "#FFFFFF", "text": "#171521",
        "muted": "#777286", "primary": "#6C4BF4", "blue": "#3B82F6",
        "green": "#10B981", "red": "#EF4444", "orange": "#F59E0B",
        "input": "#F1EFFF", "border": "#E3DFFC", "sidebar": "#171229",
        "sidebar_hover": "#2A2148", "hover": "#5838D6"
    },
    "Ocean Blue": {
        "bg": "#F2F8FF", "card": "#FFFFFF", "text": "#101B2D",
        "muted": "#6B778C", "primary": "#1479FF", "blue": "#2563EB",
        "green": "#10B981", "red": "#EF4444", "orange": "#F59E0B",
        "input": "#EDF5FF", "border": "#DCEBFF", "sidebar": "#0C1B33",
        "sidebar_hover": "#17345C", "hover": "#0B5FCC"
    },
    "Emerald Green": {
        "bg": "#F2FBF7", "card": "#FFFFFF", "text": "#10221A",
        "muted": "#6D7E75", "primary": "#059669", "blue": "#2563EB",
        "green": "#10B981", "red": "#EF4444", "orange": "#F59E0B",
        "input": "#EAF9F2", "border": "#D7F0E5", "sidebar": "#0B2118",
        "sidebar_hover": "#16432F", "hover": "#047857"
    },
    "Sunset Orange": {
        "bg": "#FFF8F2", "card": "#FFFFFF", "text": "#271912",
        "muted": "#806F67", "primary": "#F97316", "blue": "#3B82F6",
        "green": "#10B981", "red": "#EF4444", "orange": "#F59E0B",
        "input": "#FFF1E7", "border": "#F8E0CF", "sidebar": "#29160D",
        "sidebar_hover": "#4B281A", "hover": "#D85C0A"
    }
}

CATEGORIES = [
    "Food", "Shopping", "Transport", "Bills", "Entertainment",
    "Health", "Education", "Investment", "Other"
]

ICONS = {
    "Food": "🍔", "Shopping": "🛍", "Transport": "🚗", "Bills": "💡",
    "Entertainment": "🎬", "Health": "❤️", "Education": "📚",
    "Investment": "📈", "Other": "📦"
}


class ExpenseFlow:
    def __init__(self, root):
        self.root = root
        self.root.title("ExpenseFlow Pro - Money Manager")
        self.root.geometry("1450x900")
        self.root.minsize(1100, 720)

        self.theme_name = "Midnight Purple"
        self.dark_mode = False
        self.colors = dict(THEMES[self.theme_name])

        self.data = {
            "salary": [],
            "transactions": [],
            "budgets": {},
            "goals": [],
            "deleted_goals": [],
            "emergency_fund": {
                "target": 0.0,
                "saved": 0.0,
                "updated_date": ""
            },
            "emergency_fund_history": []
        }

        self.current_page = "Dashboard"
        self.load_data()
        self.setup_style()
        self.build_ui()

    # ========================================================
    # DATA
    # ========================================================

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            if isinstance(loaded, dict):
                for key in self.data:
                    if key in loaded:
                        self.data[key] = loaded[key]

                if not isinstance(self.data["salary"], list):
                    self.data["salary"] = []
                if not isinstance(self.data["transactions"], list):
                    self.data["transactions"] = []
                if not isinstance(self.data["budgets"], dict):
                    self.data["budgets"] = {}
                if not isinstance(self.data["goals"], list):
                    self.data["goals"] = []
                if not isinstance(self.data.get("deleted_goals"), list):
                    self.data["deleted_goals"] = []
                if not isinstance(self.data.get("emergency_fund"), dict):
                    self.data["emergency_fund"] = {
                        "target": 0.0, "saved": 0.0, "updated_date": ""
                    }
                else:
                    self.data["emergency_fund"].setdefault("target", 0.0)
                    self.data["emergency_fund"].setdefault("saved", 0.0)
                    self.data["emergency_fund"].setdefault("updated_date", "")
                if not isinstance(self.data.get("emergency_fund_history"), list):
                    self.data["emergency_fund_history"] = []
        except Exception:
            messagebox.showwarning(
                "Data Warning",
                "The saved data could not be read. A fresh data set will be used."
            )

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as exc:
            messagebox.showerror("Save Error", f"Could not save data:\n{exc}")

    # ========================================================
    # CALCULATIONS
    # ========================================================

    def salary_total(self):
        return sum(self.to_float(x.get("amount")) for x in self.data["salary"])

    def transaction_income(self):
        return sum(
            self.to_float(x.get("amount"))
            for x in self.data["transactions"]
            if x.get("type") == "Income"
        )

    def transaction_expenses(self):
        return sum(
            self.to_float(x.get("amount"))
            for x in self.data["transactions"]
            if x.get("type") == "Expense"
        )

    def total_spending(self):
        # Regular expenses + money set aside into goals/emergency fund.
        return (
            self.transaction_expenses()
            + self.historical_goal_saved_total()
            + self.emergency_saved_total()
        )

    def total_income(self):
        return self.salary_total() + self.transaction_income()

    def goal_saved_total(self):
        return sum(self.to_float(x.get("saved", 0)) for x in self.data["goals"])

    def goal_target_total(self):
        return sum(self.to_float(x.get("value", 0)) for x in self.data["goals"])

    def deleted_goal_saved_total(self):
        return sum(
            self.to_float(x.get("saved", 0))
            for x in self.data.get("deleted_goals", [])
        )

    def historical_goal_saved_total(self):
        return self.goal_saved_total() + self.deleted_goal_saved_total()

    def emergency_saved_total(self):
        return self.to_float(
            self.data.get("emergency_fund", {}).get("saved", 0)
        )

    def emergency_target_total(self):
        return self.to_float(
            self.data.get("emergency_fund", {}).get("target", 0)
        )

    def balance(self):
        # Money moved into savings goals is treated as money set aside,
        # so it is deducted from the available salary/income balance.
        return (
            self.total_income()
            - self.transaction_expenses()
            - self.historical_goal_saved_total()
            - self.emergency_saved_total()
        )

    def savings_rate(self):
        income = self.total_income()
        if income <= 0:
            return 0
        return max(0, (self.balance() / income) * 100)

    def monthly_salary(self, year=None, month=None):
        today = datetime.now().date()
        year = today.year if year is None else year
        month = today.month if month is None else month

        return sum(
            self.to_float(x.get("amount"))
            for x in self.data["salary"]
            if self.date_matches_month(x.get("date", ""), year, month)
        )

    def monthly_expenses(self, year=None, month=None):
        today = datetime.now().date()
        year = today.year if year is None else year
        month = today.month if month is None else month

        return sum(
            self.to_float(x.get("amount"))
            for x in self.data["transactions"]
            if x.get("type") == "Expense"
            and self.date_matches_month(x.get("date", ""), year, month)
        )

    def category_totals(self):
        totals = {}
        for item in self.data["transactions"]:
            if item.get("type") == "Expense":
                cat = item.get("category", "Other")
                totals[cat] = totals.get(cat, 0) + self.to_float(item.get("amount"))
        return totals

    def current_month_category_totals(self):
        today = datetime.now().date()
        totals = {}
        for item in self.data["transactions"]:
            if (
                item.get("type") == "Expense"
                and self.date_matches_month(item.get("date", ""), today.year, today.month)
            ):
                cat = item.get("category", "Other")
                totals[cat] = totals.get(cat, 0) + self.to_float(item.get("amount"))
        return totals

    @staticmethod
    def to_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    # ========================================================
    # UI SETUP
    # ========================================================

    def setup_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "TCombobox",
            padding=7,
            font=("Segoe UI", 10)
        )

    def build_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.configure(bg=self.colors["bg"])

        self.build_sidebar()

        self.main = tk.Frame(self.root, bg=self.colors["bg"])
        self.main.pack(side="left", fill="both", expand=True)

        self.header = tk.Frame(
            self.main,
            bg=self.colors["bg"],
            height=78
        )
        self.header.pack(fill="x", padx=28, pady=(18, 8))
        self.header.pack_propagate(False)

        self.title_label = tk.Label(
            self.header,
            text=self.current_page,
            font=("Segoe UI", 25, "bold"),
            fg=self.colors["text"],
            bg=self.colors["bg"]
        )
        self.title_label.pack(side="left", anchor="center")

        self.content = tk.Frame(
            self.main,
            bg=self.colors["bg"]
        )
        self.content.pack(
            fill="both",
            expand=True,
            padx=28,
            pady=(0, 20)
        )

        self.show_page(self.current_page)

    def build_sidebar(self):
        sidebar = tk.Frame(
            self.root,
            bg=self.colors["sidebar"],
            width=245
        )
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo = tk.Frame(sidebar, bg=self.colors["sidebar"])
        logo.pack(fill="x", padx=22, pady=(28, 30))

        tk.Label(
            logo,
            text="EF",
            font=("Segoe UI", 17, "bold"),
            fg="white",
            bg=self.colors["primary"],
            width=3,
            pady=8
        ).pack(side="left")

        brand = tk.Frame(logo, bg=self.colors["sidebar"])
        brand.pack(side="left", padx=10)

        tk.Label(
            brand, text="ExpenseFlow",
            font=("Segoe UI", 16, "bold"),
            fg="white", bg=self.colors["sidebar"]
        ).pack(anchor="w")

        tk.Label(
            brand, text="PRO MONEY MANAGER",
            font=("Segoe UI", 7, "bold"),
            fg="#A8A2BD", bg=self.colors["sidebar"]
        ).pack(anchor="w")

        self.nav_buttons = {}

        nav = [
            ("🏠", "Dashboard"),
            ("💼", "Salary"),
            ("💳", "Transactions"),
            ("＋", "Add Transaction"),
            ("🎯", "Budgets"),
            ("🛡", "Emergency Fund"),
            ("📊", "Analytics")
        ]

        for icon, text in nav:
            btn = tk.Button(
                sidebar,
                text=f"  {icon}   {text}",
                command=lambda p=text: self.show_page(p),
                anchor="w",
                font=("Segoe UI", 10, "bold"),
                fg="white",
                bg=self.colors["sidebar"],
                activeforeground="white",
                activebackground=self.colors["sidebar_hover"],
                relief="flat",
                bd=0,
                cursor="hand2",
                padx=20,
                pady=13
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[text] = btn

        tk.Frame(
            sidebar,
            height=2,
            bg=self.colors["sidebar_hover"]
        ).pack(fill="x", padx=20, pady=20)

        tk.Label(
            sidebar,
            text="QUICK ACTIONS",
            font=("Segoe UI", 8, "bold"),
            fg="#858096",
            bg=self.colors["sidebar"]
        ).pack(anchor="w", padx=25, pady=(0, 8))

        self.side_button(
            sidebar, "＋  Add Salary", self.show_salary,
            self.colors["blue"]
        )

        self.side_button(
            sidebar, "＋  Add Expense", self.show_add_transaction,
            self.colors["primary"]
        )

        bottom = tk.Frame(sidebar, bg=self.colors["sidebar"])
        bottom.pack(side="bottom", fill="x", padx=18, pady=20)

        tk.Label(
            bottom, text="Theme",
            font=("Segoe UI", 8, "bold"),
            fg="#858096", bg=self.colors["sidebar"]
        ).pack(anchor="w")

        self.theme_var = tk.StringVar(value=self.theme_name)

        combo = ttk.Combobox(
            bottom,
            textvariable=self.theme_var,
            values=list(THEMES.keys()),
            state="readonly"
        )
        combo.pack(fill="x", pady=(5, 10))
        combo.bind("<<ComboboxSelected>>", self.change_theme)

        mode_text = "☀  Light Mode" if self.dark_mode else "☾  Dark Mode"
        self.mode_button = tk.Button(
            bottom,
            text=mode_text,
            command=self.toggle_mode,
            font=("Segoe UI", 9, "bold"),
            fg="white",
            bg=self.colors["sidebar_hover"],
            activebackground=self.colors["hover"],
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=9
        )
        self.mode_button.pack(fill="x")

        self.highlight_nav()

    def side_button(self, parent, text, command, color):
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 9, "bold"),
            fg="white",
            bg=color,
            activebackground=self.colors["hover"],
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=10
        )
        btn.pack(fill="x", padx=10, pady=4)

    def highlight_nav(self):
        if not hasattr(self, "nav_buttons"):
            return
        for name, btn in self.nav_buttons.items():
            if name == self.current_page:
                btn.configure(bg=self.colors["primary"])
            else:
                btn.configure(bg=self.colors["sidebar"])

    def show_page(self, page):
        self.current_page = page
        self.highlight_nav()

        if page == "Dashboard":
            self.show_dashboard()
        elif page == "Salary":
            self.show_salary()
        elif page == "Transactions":
            self.show_transactions()
        elif page == "Add Transaction":
            self.show_add_transaction()
        elif page == "Budgets":
            self.show_budgets()
        elif page == "Emergency Fund":
            self.show_emergency_fund()
        elif page == "Analytics":
            self.show_analytics()

    # ========================================================
    # DASHBOARD
    # ========================================================

    def show_dashboard(self):
        self.title_label.config(text="Welcome back, Harshwardhan 👋")
        self.clear_content()

        # Scrollable dashboard so every card remains visible on smaller screens.
        canvas = tk.Canvas(self.content, bg=self.colors["bg"], highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(self.content, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        body = tk.Frame(canvas, bg=self.colors["bg"])
        window_id = canvas.create_window((0, 0), window=body, anchor="nw")

        def refresh_scroll(_=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def resize_body(event):
            canvas.itemconfigure(window_id, width=max(1, event.width))

        body.bind("<Configure>", refresh_scroll)
        canvas.bind("<Configure>", resize_body)

        def wheel(event):
            canvas.yview_scroll(int(-event.delta / 120), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # ---------- Welcome / search header ----------
        welcome = tk.Frame(body, bg=self.colors["bg"])
        welcome.pack(fill="x", pady=(0, 16))
        welcome.columnconfigure(0, weight=1)
        welcome.columnconfigure(1, weight=0)

        left = tk.Frame(welcome, bg=self.colors["bg"])
        left.grid(row=0, column=0, sticky="w")
        tk.Label(left, text="Here's your financial overview for today.",
                 font=("Segoe UI", 10), bg=self.colors["bg"],
                 fg=self.colors["muted"]).pack(anchor="w")

        right = tk.Frame(welcome, bg=self.colors["bg"])
        right.grid(row=0, column=1, sticky="e")
        search = tk.Entry(right, font=("Segoe UI", 10), relief="flat",
                          bg=self.colors["card"], fg=self.colors["muted"],
                          insertbackground=self.colors["text"], width=30)
        search.insert(0, "🔎  Search transactions, goals, budgets...")
        search.pack(side="left", ipady=9, padx=(0, 12))
        tk.Label(right, text="🔔", font=("Segoe UI", 18),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(side="left", padx=8)
        tk.Label(right, text="●", font=("Segoe UI", 9),
                 bg=self.colors["bg"], fg=self.colors["red"]).place(relx=.88, rely=.03)
        tk.Label(right, text="H", font=("Segoe UI", 11, "bold"),
                 bg=self.colors["primary"], fg="white", width=3, pady=7).pack(side="left", padx=8)
        tk.Label(right, text="Harshwardhan ⌄", font=("Segoe UI", 10, "bold"),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(side="left")

        # ---------- Top statistic cards ----------
        # Five cards always share the COMPLETE available width.
        # No fixed card width is used, so they resize with the window.
        stats = tk.Frame(body, bg=self.colors["bg"])
        stats.pack(fill="x", pady=(0, 14))
        for i in range(5):
            stats.grid_columnconfigure(i, weight=1, uniform="stats", minsize=0)

        total_goal_target = self.goal_target_total()
        total_goal_saved = self.historical_goal_saved_total()
        emergency_target = self.emergency_target_total()
        emergency_saved = self.emergency_saved_total()

        cards = [
            ("💰", "Available Balance", self.money(self.balance()), self.colors["primary"]),
            ("💼", "Salary", self.money(self.salary_total()), self.colors["blue"]),
            ("🔥", "Total Spending", self.money(self.total_spending()), self.colors["red"]),
            ("🎯", "Goals Saved", f"{self.money(total_goal_saved)} / {self.money(total_goal_target)}", self.colors["orange"]),
            ("🛡", "Emergency Fund", f"{self.money(emergency_saved)} / {self.money(emergency_target)}", self.colors["green"]),
        ]
        for i, card_data in enumerate(cards):
            # 5 equal columns, with only a tiny gap between cards.
            self.stat_card(stats, *card_data).grid(
                row=0, column=i, sticky="nsew", padx=(2 if i == 0 else 1, 1 if i < 4 else 2)
            )

        # ---------- Main 2-column area ----------
        middle = tk.Frame(body, bg=self.colors["bg"])
        middle.pack(fill="x", pady=(0, 14))
        middle.grid_columnconfigure(0, weight=1, uniform="main")
        middle.grid_columnconfigure(1, weight=1, uniform="main")

        overview = self.panel(middle, "📊  Spending Overview")
        overview.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        self.draw_spending_bars(overview)

        activity = self.panel(middle, "⚡  Recent Activity")
        activity.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        recent = self.all_activity()[:7]
        if not recent:
            self.empty_message(activity, "No activity yet", "Add salary or transactions to begin.")
        else:
            for item in recent:
                self.activity_row(activity, item)

        # ---------- Savings goals cards ----------
        goals_panel = self.panel(body, "🎯  Savings Goals")
        goals_panel.pack(fill="x", pady=(0, 14))

        if not self.data["goals"]:
            self.empty_message(goals_panel, "No savings goals yet",
                               "Add goals from Budgets to track your progress here.")
        else:
            goal_grid = tk.Frame(goals_panel, bg=self.colors["card"])
            goal_grid.pack(fill="x", padx=16, pady=(0, 16))
            for i in range(min(3, len(self.data["goals"]))):
                goal_grid.grid_columnconfigure(i, weight=1, uniform="goal")
            for i, goal in enumerate(self.data["goals"][:3]):
                target = self.to_float(goal.get("value", 0))
                saved = self.to_float(goal.get("saved", 0))
                percent = min((saved / target * 100) if target > 0 else 0, 100)
                card = tk.Frame(goal_grid, bg=self.colors["input"],
                                highlightbackground=self.colors["border"], highlightthickness=1)
                card.grid(row=0, column=i, sticky="nsew", padx=5)
                tk.Label(card, text=f"🏆  {goal.get('name', 'Goal')}",
                         font=("Segoe UI", 11, "bold"), bg=self.colors["input"],
                         fg=self.colors["text"]).pack(anchor="w", padx=14, pady=(12, 5))
                tk.Label(card, text=f"{self.money(saved)}  /  {self.money(target)}",
                         font=("Segoe UI", 10, "bold"), bg=self.colors["input"],
                         fg=self.colors["primary"]).pack(anchor="w", padx=14)
                track = tk.Frame(card, bg=self.colors["card"], height=8)
                track.pack(fill="x", padx=14, pady=(9, 3))
                track.pack_propagate(False)
                tk.Frame(track, bg=self.colors["green"]).place(
                    relx=0, rely=0, relheight=1, relwidth=max(.01, percent / 100))
                tk.Label(card, text=f"{percent:.1f}% completed", font=("Segoe UI", 8, "bold"),
                         bg=self.colors["input"], fg=self.colors["muted"]).pack(anchor="w", padx=14, pady=(0, 12))

        # ---------- Insight + monthly summary ----------
        bottom = tk.Frame(body, bg=self.colors["bg"])
        bottom.pack(fill="x", pady=(0, 20))
        bottom.grid_columnconfigure(0, weight=1, uniform="bottom")
        bottom.grid_columnconfigure(1, weight=1, uniform="bottom")

        insight = self.panel(bottom, "🧠  Smart Financial Insight")
        insight.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        self.insight_content(insight)

        summary = self.panel(bottom, "📅  This Month")
        summary.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        self.month_summary(summary)

        body.update_idletasks()
        refresh_scroll()
        canvas.yview_moveto(0)

    def stat_card(self, parent, icon, title, value, accent):
        card = tk.Frame(parent, bg=self.colors["card"],
                        highlightbackground=self.colors["border"], highlightthickness=1)
        top = tk.Frame(card, bg=self.colors["card"])
        top.pack(fill="x", padx=10, pady=(12, 4))

        icon_box = tk.Label(top, text=icon, font=("Segoe UI Emoji", 16),
                            bg=self.colors["input"], fg=self.colors["text"],
                            padx=5, pady=3)
        icon_box.pack(side="left")
        tk.Label(top, text=title, font=("Segoe UI", 9, "bold"),
                 bg=self.colors["card"], fg=self.colors["muted"]).pack(side="left", padx=6)

        display = value if isinstance(value, str) else self.money(value)
        # Long goal/emergency values are allowed to wrap instead of being clipped.
        value_font = ("Segoe UI", 13 if isinstance(value, str) else 19, "bold")
        value_label = tk.Label(
            card, text=display, font=value_font,
            bg=self.colors["card"], fg=accent, anchor="w", justify="left",
            wraplength=190
        )
        value_label.pack(fill="x", padx=10, pady=(2, 4))

        if title == "Goals Saved":
            target = self.to_float(total_goal_target) if False else self.goal_target_total()
            saved = self.historical_goal_saved_total()
            pct = (saved / target * 100) if target > 0 else 0
            pct = min(max(pct, 0), 100)
            track = tk.Frame(card, bg=self.colors["input"], height=6)
            track.pack(fill="x", padx=10, pady=(2, 11))
            track.pack_propagate(False)
            tk.Frame(track, bg=accent).place(relx=0, rely=0, relheight=1, relwidth=max(.01, pct/100))
        elif title == "Emergency Fund":
            target = self.emergency_target_total()
            saved = self.emergency_saved_total()
            pct = (saved / target * 100) if target > 0 else 0
            pct = min(max(pct, 0), 100)
            track = tk.Frame(card, bg=self.colors["input"], height=6)
            track.pack(fill="x", padx=10, pady=(2, 11))
            track.pack_propagate(False)
            tk.Frame(track, bg=accent).place(relx=0, rely=0, relheight=1, relwidth=max(.01, pct/100))
        else:
            tk.Label(card, text="This month", font=("Segoe UI", 8),
                     bg=self.colors["card"], fg=self.colors["muted"]).pack(anchor="w", padx=14, pady=(0, 12))
        return card

    def panel(self, parent, title):
        frame = tk.Frame(
            parent,
            bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        tk.Label(
            frame, text=title,
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["card"], fg=self.colors["text"]
        ).pack(anchor="w", padx=20, pady=(18, 12))
        return frame

    def draw_spending_bars(self, parent):
        """Premium spending donut with polished legend, progress bars and summary."""
        totals = self.current_month_category_totals()
        goal_saved = self.historical_goal_saved_total()
        emergency_saved = self.emergency_saved_total()
        if goal_saved > 0:
            totals["🎯 Goals Saved"] = goal_saved
        if emergency_saved > 0:
            totals["🛡 Emergency Fund"] = emergency_saved

        if not totals:
            self.empty_message(parent, "No spending yet", "Your spending breakdown will appear here.")
            return

        # Keep the chart readable while preserving the biggest categories.
        ordered = sorted(totals.items(), key=lambda x: x[1], reverse=True)
        if len(ordered) > 6:
            top = ordered[:5]
            other = sum(v for _, v in ordered[5:])
            if other > 0:
                top.append(("Other", other))
            ordered = top

        total = sum(v for _, v in ordered) or 1
        palette = [
            self.colors["primary"], self.colors["blue"], self.colors["orange"],
            self.colors["green"], self.colors["red"], "#8B7ACB"
        ]

        area = tk.Frame(parent, bg=self.colors["card"])
        area.pack(fill="both", expand=True, padx=14, pady=(0, 16))
        area.grid_columnconfigure(0, weight=0)
        area.grid_columnconfigure(1, weight=1)

        # ---- Premium chart card ----
        chart_box = tk.Frame(
            area, bg=self.colors["input"],
            highlightbackground=self.colors["border"], highlightthickness=1
        )
        chart_box.grid(row=0, column=0, sticky="nsew", padx=(0, 14), pady=2)

        chart = tk.Canvas(
            chart_box, width=285, height=285,
            bg=self.colors["input"], highlightthickness=0, bd=0
        )
        chart.pack(padx=8, pady=8)

        cx, cy = 142, 135
        radius = 92
        start = 90
        for i, (_, amount) in enumerate(ordered):
            extent = -360 * amount / total
            col = palette[i % len(palette)]
            # Outer soft ring
            chart.create_arc(
                cx-radius-2, cy-radius-2, cx+radius+2, cy+radius+2,
                start=start, extent=extent, style="arc", width=30,
                outline=self.colors["card"]
            )
            chart.create_arc(
                cx-radius, cy-radius, cx+radius, cy+radius,
                start=start, extent=extent, style="arc", width=25,
                outline=col
            )
            start += extent

        # Donut center
        chart.create_oval(
            cx-58, cy-58, cx+58, cy+58,
            fill=self.colors["card"], outline=self.colors["card"]
        )
        chart.create_text(
            cx, cy-14, text=self.money(total),
            font=("Segoe UI", 18, "bold"), fill=self.colors["text"]
        )
        chart.create_text(
            cx, cy+10, text="Total Spent",
            font=("Segoe UI", 9, "bold"), fill=self.colors["muted"]
        )
        chart.create_text(
            cx, cy+31, text="This Month",
            font=("Segoe UI", 8), fill=self.colors["primary"]
        )

        # Mini total badge below the chart
        badge = tk.Frame(chart_box, bg=self.colors["card"])
        badge.pack(fill="x", padx=18, pady=(0, 16))
        tk.Label(
            badge, text=f"{len(ordered)} categories",
            font=("Segoe UI", 9, "bold"), bg=self.colors["card"],
            fg=self.colors["primary"]
        ).pack(side="left", padx=10, pady=7)
        tk.Label(
            badge, text="Monthly breakdown",
            font=("Segoe UI", 8), bg=self.colors["card"],
            fg=self.colors["muted"]
        ).pack(side="right", padx=10)

        # ---- Right-side legend ----
        list_box = tk.Frame(area, bg=self.colors["card"])
        list_box.grid(row=0, column=1, sticky="nsew")

        header = tk.Frame(list_box, bg=self.colors["card"])
        header.pack(fill="x", pady=(3, 8))
        tk.Label(
            header, text="Spending Breakdown",
            font=("Segoe UI", 12, "bold"), bg=self.colors["card"],
            fg=self.colors["text"]
        ).pack(side="left")
        tk.Label(
            header, text=self.money(total),
            font=("Segoe UI", 10, "bold"), bg=self.colors["card"],
            fg=self.colors["primary"]
        ).pack(side="right")

        tk.Frame(list_box, bg=self.colors["border"], height=1).pack(fill="x", pady=(0, 7))

        for i, (category, amount) in enumerate(ordered):
            name = category.replace("🎯 ", "").replace("🛡 ", "")
            pct = amount / total * 100
            col = palette[i % len(palette)]

            card = tk.Frame(
                list_box, bg=self.colors["input"],
                highlightbackground=self.colors["border"], highlightthickness=1
            )
            card.pack(fill="x", pady=4)

            top = tk.Frame(card, bg=self.colors["input"])
            top.pack(fill="x", padx=10, pady=(7, 3))
            tk.Label(
                top, text="●", font=("Segoe UI", 11, "bold"),
                bg=self.colors["input"], fg=col
            ).pack(side="left")
            tk.Label(
                top, text=name, font=("Segoe UI", 9, "bold"),
                bg=self.colors["input"], fg=self.colors["text"]
            ).pack(side="left", padx=6)
            tk.Label(
                top, text=f"{self.money(amount)}  ({pct:.1f}%)",
                font=("Segoe UI", 8, "bold"), bg=self.colors["input"],
                fg=self.colors["text"]
            ).pack(side="right")

            track = tk.Frame(card, bg=self.colors["border"], height=6)
            track.pack(fill="x", padx=10, pady=(0, 8))
            track.pack_propagate(False)
            tk.Frame(track, bg=col).place(
                relx=0, rely=0, relheight=1,
                relwidth=max(.015, min(1, pct / 100))
            )

    def all_activity(self):
        items = []

        for x in self.data["salary"]:
            items.append({
                "kind": "Salary",
                "id": x.get("id", 0),
                "company": x.get("company", "Salary"),
                "amount": x.get("amount", 0),
                "date": x.get("date", "")
            })

        for x in self.data["transactions"]:
            item = dict(x)
            item["kind"] = "Transaction"
            items.append(item)

        # Show each active savings goal.
        for x in self.data["goals"]:
            saved = self.to_float(x.get("saved", 0))
            if saved > 0:
                items.append({
                    "kind": "Goal",
                    "id": f"goal_{x.get('id', '')}",
                    "name": x.get("name", "Savings Goal"),
                    "amount": saved,
                    "date": x.get("updated_date", x.get("date", "")),
                    "status": "Active"
                })

        # Keep deleted goals visible in Recent Activity for historical reporting.
        for x in self.data.get("deleted_goals", []):
            saved = self.to_float(x.get("saved", 0))
            if saved > 0:
                items.append({
                    "kind": "Deleted Goal",
                    "id": f"deleted_goal_{x.get('id', '')}_{x.get('deleted_date', '')}",
                    "name": x.get("name", "Deleted Savings Goal"),
                    "amount": saved,
                    "date": x.get("deleted_date", x.get("updated_date", x.get("date", ""))),
                    "status": "Deleted"
                })

        # Show emergency fund activity when money has been set aside.
        emergency_saved = self.emergency_saved_total()
        if emergency_saved > 0:
            ef = self.data.get("emergency_fund", {})
            items.append({
                "kind": "Emergency Fund",
                "id": "emergency_fund",
                "name": "Emergency Fund",
                "amount": emergency_saved,
                "date": ef.get("updated_date", "")
            })

        return sorted(
            items,
            key=lambda x: (x.get("date", ""), str(x.get("id", ""))),
            reverse=True
        )

    def activity_row(self, parent, item):
        row = tk.Frame(parent, bg=self.colors["card"])
        row.pack(fill="x", padx=18, pady=5)

        if item["kind"] == "Salary":
            title = item.get("company", "Salary")
            subtitle = f"Salary • {item.get('date', '')}"
            sign, color, icon = "+", self.colors["green"], "💼"

        elif item["kind"] == "Goal":
            title = item.get("name", "Savings Goal")
            subtitle = f"Savings Goal • {item.get('date', '') or 'Saved Value'}"
            sign, color, icon = "+", self.colors["green"], "🎯"

        elif item["kind"] == "Deleted Goal":
            title = item.get("name", "Deleted Savings Goal")
            subtitle = f"Goal Deleted • {item.get('date', '') or 'Historical'}"
            sign, color, icon = "-", self.colors["orange"], "🗑"

        elif item["kind"] == "Emergency Fund":
            title = "Emergency Fund"
            subtitle = f"Emergency Fund • {item.get('date', '') or 'Saved Value'}"
            sign, color, icon = "-", self.colors["green"], "🛡"

        else:
            title = item.get("description", "Transaction")
            subtitle = f"{item.get('category', 'Other')} • {item.get('date', '')}"
            if item.get("type") == "Income":
                sign, color = "+", self.colors["green"]
            else:
                sign, color = "-", self.colors["red"]
            icon = ICONS.get(item.get("category"), "💸")

        tk.Label(
            row, text=icon, font=("Segoe UI", 13),
            bg=self.colors["input"], fg=self.colors["text"],
            width=3, pady=4
        ).pack(side="left")

        info = tk.Frame(row, bg=self.colors["card"])
        info.pack(side="left", padx=9)

        tk.Label(
            info, text=title[:28],
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["card"], fg=self.colors["text"]
        ).pack(anchor="w")

        tk.Label(
            info, text=subtitle,
            font=("Segoe UI", 8),
            bg=self.colors["card"], fg=self.colors["muted"]
        ).pack(anchor="w")

        tk.Label(
            row,
            text=f"{sign}{self.money(item.get('amount', 0))}",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["card"], fg=color
        ).pack(side="right")

    def insight_content(self, parent):
        if not self.data["salary"] and not self.data["transactions"]:
            text = "Start by adding your salary and daily transactions."
        elif self.transaction_expenses() == 0:
            text = "Great start! You have recorded income but no expenses yet."
        else:
            categories = self.category_totals()
            top = max(categories, key=categories.get) if categories else None
            rate = self.savings_rate()

            if rate >= 30:
                text = f"Excellent saving rate: {rate:.1f}%. Keep your spending under control."
            elif rate >= 15:
                text = f"Good progress: {rate:.1f}% of your income remains after expenses."
            elif rate > 0:
                text = f"Your savings rate is {rate:.1f}%. Consider reducing non-essential spending."
            else:
                text = "Your expenses are currently equal to or higher than your income."

            if top:
                text += f" Biggest spending category: {top}."

        tk.Label(
            parent,
            text=text,
            font=("Segoe UI", 10),
            wraplength=500,
            justify="left",
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).pack(anchor="w", padx=20, pady=(0, 20))

        tk.Label(
            parent,
            text=f"Savings Rate: {self.savings_rate():.1f}%",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["card"],
            fg=self.colors["green"] if self.savings_rate() >= 15 else self.colors["orange"]
        ).pack(anchor="w", padx=20, pady=(0, 18))

    def month_summary(self, parent):
        salary = self.monthly_salary()
        expenses = self.monthly_expenses()
        remaining = salary - expenses

        rows = [
            ("Salary", salary, self.colors["blue"]),
            ("Expenses", expenses, self.colors["red"]),
            ("Remaining", remaining, self.colors["green"] if remaining >= 0 else self.colors["red"])
        ]

        for title, amount, color in rows:
            row = tk.Frame(parent, bg=self.colors["card"])
            row.pack(fill="x", padx=20, pady=4)
            tk.Label(
                row, text=title,
                font=("Segoe UI", 9),
                bg=self.colors["card"], fg=self.colors["muted"]
            ).pack(side="left")
            tk.Label(
                row, text=self.money(amount),
                font=("Segoe UI", 10, "bold"),
                bg=self.colors["card"], fg=color
            ).pack(side="right")

    # ========================================================
    # SALARY
    # ========================================================

    def show_salary(self):
        self.title_label.config(text="Salary Management")
        self.clear_content()

        total = self.salary_total()
        monthly = self.monthly_salary()

        stats = tk.Frame(self.content, bg=self.colors["bg"])
        stats.pack(fill="x")

        self.stat_card(
            stats, "💼", "All Salary Records", total, self.colors["blue"]
        ).grid(row=0, column=0, sticky="nsew", padx=5)
        self.stat_card(
            stats, "📅", "This Month", monthly, self.colors["green"]
        ).grid(row=0, column=1, sticky="nsew", padx=5)

        stats.columnconfigure(0, weight=1)
        stats.columnconfigure(1, weight=1)

        form = self.panel(self.content, "＋  Add New Salary")
        form.pack(fill="x", pady=12)

        grid = tk.Frame(form, bg=self.colors["card"])
        grid.pack(fill="x", padx=20, pady=5)

        self.salary_company = self.input_box(grid, "Company / Source", 0)
        self.salary_amount = self.input_box(grid, "Salary Amount (₹)", 1)
        self.salary_date = self.input_box(grid, "Salary Date", 2)
        self.salary_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        for i in range(3):
            grid.columnconfigure(i, weight=1)

        self.modern_button(
            form, "✓  Add Salary", self.add_salary, self.colors["blue"]
        ).pack(fill="x", padx=20, pady=18)

        history = self.panel(self.content, "🧾  Salary History")
        history.pack(fill="both", expand=True)

        if not self.data["salary"]:
            self.empty_message(history, "No salary records", "Add your first salary above.")
            return

        for item in sorted(
            self.data["salary"],
            key=lambda x: x.get("date", ""),
            reverse=True
        ):
            self.salary_row(history, item)

    # ========================================================
    # TRANSACTION FORM
    # ========================================================

    def show_add_transaction(self):
        self.title_label.config(text="Add Transaction")
        self.clear_content()

        panel = self.panel(self.content, "＋  Add New Transaction")
        panel.pack(fill="x", pady=5)

        tk.Label(
            panel,
            text="Track an expense or additional income.",
            font=("Segoe UI", 9),
            bg=self.colors["card"], fg=self.colors["muted"]
        ).pack(anchor="w", padx=20)

        grid = tk.Frame(panel, bg=self.colors["card"])
        grid.pack(fill="x", padx=20, pady=20)

        self.transaction_description = self.input_box(
            grid, "Description", 0, 0
        )
        self.transaction_amount = self.input_box(
            grid, "Amount (₹)", 1, 0
        )

        self.form_label(grid, "Transaction Type", 2, 0)
        self.transaction_type = tk.StringVar(value="Expense")
        ttk.Combobox(
            grid,
            textvariable=self.transaction_type,
            values=["Expense", "Income"],
            state="readonly"
        ).grid(row=1, column=2, sticky="ew", padx=5, pady=(0, 8), ipady=7)

        self.form_label(grid, "Category", 0, 2)
        self.transaction_category = tk.StringVar(value="Food")
        ttk.Combobox(
            grid,
            textvariable=self.transaction_category,
            values=CATEGORIES,
            state="readonly"
        ).grid(row=3, column=0, sticky="ew", padx=5, ipady=7)

        self.transaction_date = self.input_box(
            grid, "Date", 1, 2
        )
        self.transaction_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        for i in range(3):
            grid.columnconfigure(i, weight=1)

        self.modern_button(
            panel, "✓  Save Transaction",
            self.add_transaction, self.colors["primary"]
        ).pack(fill="x", padx=20, pady=(0, 20))

        tip = self.panel(self.content, "💡  Quick Tip")
        tip.pack(fill="x", pady=12)

        tk.Label(
            tip,
            text="Use YYYY-MM-DD for dates. ExpenseFlow saves your records automatically.",
            font=("Segoe UI", 9),
            bg=self.colors["card"], fg=self.colors["muted"]
        ).pack(anchor="w", padx=20, pady=(0, 18))

    # ========================================================
    # TRANSACTIONS
    # ========================================================

    def show_transactions(self):
        self.title_label.config(text="Transactions")
        self.clear_content()

        panel = self.panel(self.content, "💳  All Transactions")
        panel.pack(fill="both", expand=True)

        top = tk.Frame(panel, bg=self.colors["card"])
        top.pack(fill="x", padx=20, pady=(0, 8))

        self.modern_button(
            top, "＋ Add Transaction",
            self.show_add_transaction, self.colors["primary"]
        ).pack(side="right")

        filter_box = tk.Frame(panel, bg=self.colors["input"])
        filter_box.pack(fill="x", padx=20, pady=8)

        tk.Label(
            filter_box, text="🔎 Search",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["input"], fg=self.colors["text"]
        ).pack(side="left", padx=(12, 5))

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            filter_box, textvariable=self.search_var,
            font=("Segoe UI", 10),
            bg=self.colors["card"], fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat", width=18
        )
        self.search_entry.pack(side="left", padx=5, pady=8, ipady=6)

        tk.Label(
            filter_box, text="Type",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["input"], fg=self.colors["text"]
        ).pack(side="left", padx=(12, 5))

        self.type_filter_var = tk.StringVar(value="All Types")
        self.type_filter = ttk.Combobox(
            filter_box, textvariable=self.type_filter_var,
            values=["All Types", "Expense", "Income"],
            state="readonly", width=12
        )
        self.type_filter.pack(side="left", padx=5, pady=8, ipady=4)
        self.type_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh_transactions())

        tk.Label(
            filter_box, text="Category",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["input"], fg=self.colors["text"]
        ).pack(side="left", padx=(12, 5))

        self.category_filter_var = tk.StringVar(value="All Categories")
        self.category_filter = ttk.Combobox(
            filter_box, textvariable=self.category_filter_var,
            values=["All Categories"] + CATEGORIES,
            state="readonly", width=16
        )
        self.category_filter.pack(side="left", padx=5, pady=8, ipady=4)
        self.category_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh_transactions())

        tk.Label(
            filter_box, text="Date",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["input"], fg=self.colors["text"]
        ).pack(side="left", padx=(12, 5))

        self.date_filter_var = tk.StringVar(value="All Dates")
        self.date_filter = ttk.Combobox(
            filter_box, textvariable=self.date_filter_var,
            values=[
                "All Dates", "Today", "Yesterday",
                "This Month", "Last Month", "Custom Date"
            ],
            state="readonly", width=14
        )
        self.date_filter.pack(side="left", padx=5, pady=8, ipady=4)
        self.date_filter.bind("<<ComboboxSelected>>", self.date_filter_changed)

        self.custom_date_var = tk.StringVar()
        self.custom_date_entry = tk.Entry(
            filter_box, textvariable=self.custom_date_var,
            font=("Segoe UI", 9),
            bg=self.colors["card"], fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat", width=12
        )

        self.modern_button(
            filter_box, "✕ Clear", self.clear_filters, self.colors["red"]
        ).pack(side="right", padx=10)

        self.result_label = tk.Label(
            panel, text="",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["card"], fg=self.colors["muted"]
        )
        self.result_label.pack(anchor="w", padx=20, pady=(5, 0))

        self.transaction_list = tk.Frame(panel, bg=self.colors["card"])
        self.transaction_list.pack(fill="both", expand=True, padx=20, pady=8)

        self.search_var.trace_add("write", lambda *_: self.refresh_transactions())
        self.custom_date_var.trace_add("write", lambda *_: self.refresh_transactions())

        self.refresh_transactions()

    def date_filter_changed(self, event=None):
        if self.date_filter_var.get() == "Custom Date":
            self.custom_date_entry.pack(side="left", padx=5, pady=8, ipady=6)
            self.custom_date_entry.focus()
        else:
            self.custom_date_entry.pack_forget()
        self.refresh_transactions()

    def clear_filters(self):
        self.search_var.set("")
        self.type_filter_var.set("All Types")
        self.category_filter_var.set("All Categories")
        self.date_filter_var.set("All Dates")
        self.custom_date_var.set("")
        self.custom_date_entry.pack_forget()
        self.refresh_transactions()

    def refresh_transactions(self):
        if not hasattr(self, "transaction_list"):
            return

        for widget in self.transaction_list.winfo_children():
            widget.destroy()

        search = self.search_var.get().lower().strip()
        type_filter = self.type_filter_var.get()
        category_filter = self.category_filter_var.get()
        date_filter = self.date_filter_var.get()

        records = list(self.data["transactions"])

        if search:
            records = [
                x for x in records
                if search in x.get("description", "").lower()
                or search in x.get("category", "").lower()
                or search in x.get("type", "").lower()
            ]

        if type_filter != "All Types":
            records = [x for x in records if x.get("type") == type_filter]

        if category_filter != "All Categories":
            records = [x for x in records if x.get("category") == category_filter]

        today = datetime.now().date()

        if date_filter == "Today":
            records = [
                x for x in records
                if self.is_same_date(x.get("date", ""), today)
            ]
        elif date_filter == "Yesterday":
            yesterday = today - timedelta(days=1)
            records = [
                x for x in records
                if self.is_same_date(x.get("date", ""), yesterday)
            ]
        elif date_filter == "This Month":
            records = [
                x for x in records
                if self.is_this_month(x.get("date", ""))
            ]
        elif date_filter == "Last Month":
            records = [
                x for x in records
                if self.is_last_month(x.get("date", ""))
            ]
        elif date_filter == "Custom Date":
            custom = self.custom_date_var.get().strip()
            if custom:
                records = [x for x in records if x.get("date") == custom]

        records.sort(
            key=lambda x: (x.get("date", ""), str(x.get("id", ""))),
            reverse=True
        )

        self.result_label.config(
            text=f"Showing {len(records)} transaction(s)"
        )

        if not records:
            self.empty_message(
                self.transaction_list,
                "No transactions found",
                "Try changing your search or filters."
            )
            return

        for item in records:
            self.transaction_row(self.transaction_list, item)

    # ========================================================
    # BUDGETS & GOALS
    # ========================================================

    def _make_scrollable_page(self):
        """Create a full-page vertical scroller and return its inner frame."""
        self.clear_content()
        canvas = tk.Canvas(
            self.content, bg=self.colors["bg"], highlightthickness=0, bd=0
        )
        scrollbar = ttk.Scrollbar(
            self.content, orient="vertical", command=canvas.yview
        )
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        body = tk.Frame(canvas, bg=self.colors["bg"])
        window_id = canvas.create_window((0, 0), window=body, anchor="nw")

        def update_scroll(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def resize_body(event):
            canvas.itemconfigure(window_id, width=max(1, event.width))

        body.bind("<Configure>", update_scroll)
        canvas.bind("<Configure>", resize_body)

        def wheel(event):
            step = -1 if event.delta > 0 else 1
            canvas.yview_scroll(step * 3, "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        return body, canvas

    def show_budgets(self):
        self.title_label.config(text="Budgets & Goals")
        outer_content = self.content
        body, canvas = self._make_scrollable_page()
        self.content = body
        try:
            self._show_budgets_content()
        finally:
            self.content = outer_content
        body.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.yview_moveto(0)

    def _show_budgets_content(self):
        self.title_label.config(text="Budgets & Goals")
        self.clear_content()

        budget_panel = self.panel(self.content, "💰  Monthly Budgets")
        budget_panel.pack(fill="x", pady=5)

        budget_form = tk.Frame(budget_panel, bg=self.colors["card"])
        budget_form.pack(fill="x", padx=20, pady=5)

        self.form_label(budget_form, "Category", 0, 0, pack_mode=False)
        self.budget_category = tk.StringVar(value=CATEGORIES[0])
        ttk.Combobox(
            budget_form, textvariable=self.budget_category,
            values=CATEGORIES, state="readonly"
        ).grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 8), ipady=6)

        self.form_label(budget_form, "Budget Amount (₹)", 1, 0, pack_mode=False)
        self.budget_amount = tk.Entry(
            budget_form, font=("Segoe UI", 10), bg=self.colors["input"],
            fg=self.colors["text"], insertbackground=self.colors["text"], relief="flat"
        )
        self.budget_amount.grid(row=1, column=1, sticky="ew", padx=5, pady=(0, 8), ipady=8)
        budget_form.columnconfigure(0, weight=1)
        budget_form.columnconfigure(1, weight=1)

        self.modern_button(
            budget_panel, "✓  Save Budget", self.save_budget, self.colors["blue"]
        ).pack(fill="x", padx=20, pady=12)

        budget_list = self.panel(self.content, "📊  Budget Overview")
        budget_list.pack(fill="x", pady=8)
        current = self.current_month_category_totals()

        if not self.data["budgets"]:
            self.empty_message(
                budget_list, "No budgets yet",
                "Create a monthly budget above."
            )
        else:
            for category, limit in self.data["budgets"].items():
                limit = self.to_float(limit)
                spent = self.to_float(current.get(category, 0))
                ratio = spent / limit if limit > 0 else 0
                self.budget_row(budget_list, category, limit, spent, ratio)

        # GOALS
        goal_panel = self.panel(self.content, "🎯  Savings Goals")
        goal_panel.pack(fill="x", pady=8)

        # Clean 3-column goal form
        goal_form = tk.Frame(goal_panel, bg=self.colors["card"])
        goal_form.pack(fill="x", padx=20, pady=(8, 4))

        self.form_label(goal_form, "Goal Name", 0, 0, pack_mode=False)
        self.form_label(goal_form, "Goal Value (₹)", 1, 0, pack_mode=False)
        self.form_label(goal_form, "Current Saved Value (₹)", 2, 0, pack_mode=False)

        self.goal_name = tk.Entry(
            goal_form, font=("Segoe UI", 10),
            bg=self.colors["input"], fg=self.colors["text"],
            insertbackground=self.colors["text"], relief="flat"
        )
        self.goal_name.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 10), ipady=9)

        self.goal_value = tk.Entry(
            goal_form, font=("Segoe UI", 10),
            bg=self.colors["input"], fg=self.colors["text"],
            insertbackground=self.colors["text"], relief="flat"
        )
        self.goal_value.grid(row=1, column=1, sticky="ew", padx=5, pady=(0, 10), ipady=9)

        self.goal_saved = tk.Entry(
            goal_form, font=("Segoe UI", 10),
            bg=self.colors["input"], fg=self.colors["text"],
            insertbackground=self.colors["text"], relief="flat"
        )
        self.goal_saved.grid(row=1, column=2, sticky="ew", padx=5, pady=(0, 10), ipady=9)

        for col in range(3):
            goal_form.columnconfigure(col, weight=1)

        self.modern_button(
            goal_panel, "✓  Add Goal", self.add_goal, self.colors["primary"]
        ).pack(fill="x", padx=20, pady=(4, 14))

        goal_list = tk.Frame(goal_panel, bg=self.colors["card"])
        goal_list.pack(fill="x", padx=20, pady=(0, 14))

        if not self.data["goals"]:
            self.empty_message(
                goal_list, "No savings goals yet",
                "Add a goal name and target value above."
            )
        else:
            for goal in self.data["goals"]:
                self.goal_row(goal_list, goal)

    def save_budget(self):
        category = self.budget_category.get().strip()
        try:
            amount = float(self.budget_amount.get().strip())
            if not category or amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            messagebox.showerror(
                "Invalid Budget", "Enter a valid positive budget amount."
            )
            return

        self.data["budgets"][category] = amount
        self.save_data()
        messagebox.showinfo(
            "Budget Saved", f"{category} budget saved successfully."
        )
        self.show_budgets()

    def budget_row(self, parent, category, limit, spent, ratio):
        row = tk.Frame(parent, bg=self.colors["card"])
        row.pack(fill="x", padx=20, pady=7)

        tk.Label(
            row, text=f"{ICONS.get(category, '📦')}  {category}",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["card"], fg=self.colors["text"]
        ).pack(side="left")

        status = "OVER BUDGET" if spent > limit else f"{self.money(limit - spent)} left"
        status_color = self.colors["red"] if spent > limit else self.colors["green"]

        tk.Button(
            row, text="🗑", command=lambda c=category: self.delete_budget(c),
            font=("Segoe UI", 9, "bold"), fg="white",
            bg=self.colors["red"], activebackground=self.colors["hover"],
            activeforeground="white", relief="flat", bd=0,
            cursor="hand2", padx=8, pady=4
        ).pack(side="right", padx=(8, 0))

        tk.Label(
            row, text=f"{self.money(spent)} / {self.money(limit)}  •  {status}",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["card"], fg=status_color
        ).pack(side="right")

        track = tk.Frame(parent, bg=self.colors["input"], height=9)
        track.pack(fill="x", padx=20, pady=(0, 3))
        track.pack_propagate(False)

        fill = tk.Frame(
            track,
            bg=self.colors["red"] if ratio > 1 else self.colors["primary"]
        )
        fill.place(
            relx=0, rely=0, relheight=1,
            relwidth=min(max(ratio, 0.0), 1.0)
        )

    def delete_budget(self, category):
        if not messagebox.askyesno(
            "Delete Budget",
            f"Delete the {category} budget?"
        ):
            return

        self.data["budgets"].pop(category, None)
        self.save_data()
        self.show_budgets()

    def add_goal(self):
        name = self.goal_name.get().strip()
        value_text = self.goal_value.get().strip()
        saved_text = self.goal_saved.get().strip() or "0"

        if not name:
            messagebox.showerror("Invalid Goal", "Enter a goal name.")
            return

        try:
            target = float(value_text)
            saved = float(saved_text)
            if target <= 0 or saved < 0 or saved > target:
                raise ValueError
        except (ValueError, TypeError):
            messagebox.showerror(
                "Invalid Goal Value",
                "Enter a valid target value and saved value (saved cannot exceed target)."
            )
            return

        self.data["goals"].append({
            "id": datetime.now().timestamp(),
            "name": name,
            "value": target,
            "saved": saved,
            "updated_date": datetime.now().strftime("%Y-%m-%d")
        })
        self.save_data()
        messagebox.showinfo("Goal Added", f"'{name}' goal added successfully.")
        self.show_budgets()

    def goal_row(self, parent, goal):
        target = float(goal.get("value", 0) or 0)
        saved = float(goal.get("saved", 0) or 0)
        percent = (saved / target * 100) if target > 0 else 0
        percent = min(max(percent, 0), 100)

        # Card-style goal row
        row = tk.Frame(
            parent, bg=self.colors["card"],
            highlightbackground=self.colors["border"], highlightthickness=1
        )
        row.pack(fill="x", pady=10)
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)
        row.columnconfigure(2, weight=0)

        # Goal name + progress
        left = tk.Frame(row, bg=self.colors["card"])
        left.grid(row=0, column=0, sticky="ew", padx=(14, 10), pady=12)

        tk.Label(
            left, text=goal.get("name", "Goal"),
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["card"], fg=self.colors["text"]
        ).pack(anchor="w")

        # Progress bar
        style = ttk.Style()
        style.configure(
            "Goal.Horizontal.TProgressbar",
            troughcolor=self.colors["input"],
            background=self.colors["green"],
            bordercolor=self.colors["input"],
            lightcolor=self.colors["green"],
            darkcolor=self.colors["green"],
            thickness=9
        )
        progress = ttk.Progressbar(
            left, maximum=100, value=percent,
            style="Goal.Horizontal.TProgressbar"
        )
        progress.pack(fill="x", pady=(8, 4))

        status_text = "Goal completed 🎉" if percent >= 100 else f"{percent:.1f}% completed"
        status_color = self.colors["green"] if percent >= 100 else self.colors["muted"]
        tk.Label(
            left, text=status_text,
            font=("Segoe UI", 8, "bold"),
            bg=self.colors["card"], fg=status_color
        ).pack(anchor="w")

        # Amount summary
        amounts = tk.Frame(row, bg=self.colors["card"])
        amounts.grid(row=0, column=1, sticky="ew", padx=10, pady=12)

        tk.Label(
            amounts, text="SAVED",
            font=("Segoe UI", 8, "bold"),
            bg=self.colors["card"], fg=self.colors["muted"]
        ).grid(row=0, column=0, sticky="w", padx=(0, 28))
        tk.Label(
            amounts, text="TARGET",
            font=("Segoe UI", 8, "bold"),
            bg=self.colors["card"], fg=self.colors["muted"]
        ).grid(row=0, column=1, sticky="w")

        tk.Label(
            amounts, text=self.money(saved),
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["card"], fg=self.colors["green"]
        ).grid(row=1, column=0, sticky="w", padx=(0, 28), pady=(3, 0))
        tk.Label(
            amounts, text=self.money(target),
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["card"], fg=self.colors["text"]
        ).grid(row=1, column=1, sticky="w", pady=(3, 0))

        # Action buttons
        actions = tk.Frame(row, bg=self.colors["card"])
        actions.grid(row=0, column=2, sticky="e", padx=(6, 14), pady=12)

        add_btn = tk.Button(
            actions, text="＋ Add Value",
            command=lambda gid=goal.get("id"): self.add_goal_value(gid),
            font=("Segoe UI", 9, "bold"), fg="white",
            bg=self.colors["green"], activebackground=self.colors["hover"],
            activeforeground="white", relief="flat", bd=0,
            cursor="hand2", padx=12, pady=7
        )
        add_btn.pack(fill="x", pady=(0, 5))

        edit_btn = tk.Button(
            actions, text="✏  Edit",
            command=lambda gid=goal.get("id"): self.edit_goal(gid),
            font=("Segoe UI", 9, "bold"), fg="white",
            bg=self.colors["blue"], activebackground=self.colors["hover"],
            activeforeground="white", relief="flat", bd=0,
            cursor="hand2", padx=12, pady=7
        )
        edit_btn.pack(fill="x", pady=(0, 5))

        delete_btn = tk.Button(
            actions, text="🗑  Delete",
            command=lambda gid=goal.get("id"): self.delete_goal(gid),
            font=("Segoe UI", 9, "bold"), fg="white",
            bg=self.colors["red"], activebackground=self.colors["hover"],
            activeforeground="white", relief="flat", bd=0,
            cursor="hand2", padx=12, pady=7
        )
        delete_btn.pack(fill="x")

    def add_goal_value(self, goal_id):
        goal = next((g for g in self.data["goals"] if g.get("id") == goal_id), None)
        if not goal:
            return

        target = float(goal.get("value", 0) or 0)
        saved = float(goal.get("saved", 0) or 0)
        amount = simpledialog.askfloat(
            "Add Goal Value",
            f"How much do you want to add to '{goal.get('name', 'Goal')}'?",
            minvalue=0.01,
            parent=self.root
        )
        if amount is None:
            return
        if saved + amount > target:
            messagebox.showerror(
                "Target Exceeded",
                f"You can add maximum {self.money(target - saved)} to this goal."
            )
            return

        goal["saved"] = saved + amount
        goal["updated_date"] = datetime.now().strftime("%Y-%m-%d")
        self.save_data()
        self.show_budgets()

    def edit_goal(self, goal_id):
        goal = next(
            (g for g in self.data["goals"] if g.get("id") == goal_id),
            None
        )
        if not goal:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Savings Goal")
        dialog.geometry("520x440")
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors["bg"])
        dialog.transient(self.root)
        dialog.grab_set()

        panel = tk.Frame(
            dialog, bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        panel.pack(fill="both", expand=True, padx=18, pady=18)

        tk.Label(
            panel, text="✏  Edit Savings Goal",
            font=("Segoe UI", 18, "bold"),
            bg=self.colors["card"], fg=self.colors["text"]
        ).pack(anchor="w", padx=20, pady=(20, 15))

        name_entry = self.dialog_entry(
            panel, "Goal Name", goal.get("name", "")
        )
        target_entry = self.dialog_entry(
            panel, "Goal Value (₹)", str(goal.get("value", ""))
        )
        saved_entry = self.dialog_entry(
            panel, "Current Saved Value (₹)", str(goal.get("saved", ""))
        )

        def save_edit():
            name = name_entry.get().strip()
            try:
                target = float(target_entry.get().strip())
                saved = float(saved_entry.get().strip() or "0")
                if not name or target <= 0 or saved < 0 or saved > target:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Invalid Goal",
                    "Enter a name, positive target, and saved value between 0 and target.",
                    parent=dialog
                )
                return

            goal["name"] = name
            goal["value"] = target
            goal["saved"] = saved
            goal["updated_date"] = datetime.now().strftime("%Y-%m-%d")
            self.save_data()
            dialog.destroy()
            self.show_budgets()

        self.modern_button(
            panel, "✓  Save Goal Changes", save_edit, self.colors["primary"]
        ).pack(fill="x", padx=20, pady=18)

    def delete_goal(self, goal_id):
        goal = next(
            (g for g in self.data["goals"] if g.get("id") == goal_id),
            None
        )
        if not goal:
            return

        if not messagebox.askyesno(
            "Delete Goal",
            f"Delete '{goal.get('name', 'this savings goal')}'?\n\n"
            "Its saved amount will remain visible in Spending Overview "
            "and Recent Activity as historical data."
        ):
            return

        archived = dict(goal)
        archived["deleted_date"] = datetime.now().strftime("%Y-%m-%d")
        archived["status"] = "Deleted"
        self.data.setdefault("deleted_goals", []).append(archived)

        self.data["goals"] = [
            g for g in self.data["goals"] if g.get("id") != goal_id
        ]
        self.save_data()
        self.show_budgets()

    # ========================================================
    # EMERGENCY FUND
    # ========================================================

    def emergency_fund_history_total(self):
        return sum(
            self.to_float(x.get("amount", 0))
            for x in self.data.get("emergency_fund_history", [])
        )

    def show_emergency_fund(self):
        self.title_label.config(text="Emergency Fund")
        outer_content = self.content
        body, canvas = self._make_scrollable_page()
        self.content = body
        try:
            self._show_emergency_fund_content()
        finally:
            self.content = outer_content
        body.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.yview_moveto(0)

    def _show_emergency_fund_content(self):
        self.title_label.config(text="Emergency Fund")
        self.clear_content()

        ef = self.data.get("emergency_fund", {})
        target = self.emergency_target_total()
        saved = self.emergency_saved_total()
        remaining = max(target - saved, 0)
        percent = min((saved / target * 100) if target > 0 else 0, 100)

        stats = tk.Frame(self.content, bg=self.colors["bg"])
        stats.pack(fill="x", pady=5)

        stat_items = [
            ("🛡", "Fund Saved", saved, self.colors["green"]),
            ("🎯", "Target", target, self.colors["blue"]),
            ("📌", "Remaining", remaining, self.colors["orange"]),
            ("📈", "Progress", f"{percent:.1f}%", self.colors["primary"])
        ]
        for i, (icon, title, value, color) in enumerate(stat_items):
            self.stat_card(stats, icon, title, value, color).grid(
                row=0, column=i, sticky="nsew", padx=5
            )
            stats.columnconfigure(i, weight=1)

        panel = self.panel(self.content, "🛡  Emergency Fund")
        panel.pack(fill="x", pady=12)

        form = tk.Frame(panel, bg=self.colors["card"])
        form.pack(fill="x", padx=20, pady=10)
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        target_entry = self.input_box(form, "Target Amount (₹)", 0)
        target_entry.insert(0, str(target))

        amount_entry = self.input_box(form, "Amount to Add (₹)", 1)

        buttons = tk.Frame(panel, bg=self.colors["card"])
        buttons.pack(fill="x", padx=20, pady=(5, 18))

        def add_amount():
            try:
                amount = float(amount_entry.get().strip())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Invalid Amount",
                    "Enter a valid amount greater than 0."
                )
                return

            new_target_text = target_entry.get().strip()
            try:
                new_target = float(new_target_text)
                if new_target < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Invalid Target",
                    "Enter a valid target amount."
                )
                return

            new_saved = saved + amount
            if new_target > 0 and new_saved > new_target:
                messagebox.showerror(
                    "Target Exceeded",
                    "Added amount cannot make the Emergency Fund exceed its target."
                )
                return

            today = datetime.now().strftime("%Y-%m-%d")
            self.data["emergency_fund"] = {
                "target": new_target,
                "saved": new_saved,
                "updated_date": today
            }
            self.data.setdefault("emergency_fund_history", []).append({
                "id": f"ef_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                "amount": amount,
                "date": today
            })
            self.save_data()
            amount_entry.delete(0, "end")
            self.show_emergency_fund()

        def edit_fund():
            try:
                new_target = float(target_entry.get().strip())
                new_saved = float(
                    amount_entry.get().strip() or str(saved)
                )
                if new_target < 0 or new_saved < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Invalid Emergency Fund",
                    "Enter valid target and saved amounts."
                )
                return

            if new_target > 0 and new_saved > new_target:
                messagebox.showerror(
                    "Invalid Amount",
                    "Saved amount cannot be greater than the target."
                )
                return

            old_saved = saved
            difference = new_saved - old_saved
            today = datetime.now().strftime("%Y-%m-%d")

            self.data["emergency_fund"] = {
                "target": new_target,
                "saved": new_saved,
                "updated_date": today
            }

            # Keep history synchronized so Edit/Delete affects the total
            # emergency-fund amount correctly.
            history = self.data.setdefault("emergency_fund_history", [])
            if difference > 0:
                history.append({
                    "id": f"ef_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                    "amount": difference,
                    "date": today
                })
            elif difference < 0:
                remaining_to_remove = abs(difference)
                for record in reversed(history):
                    record_amount = self.to_float(record.get("amount", 0))
                    if record_amount <= 0:
                        continue
                    reduction = min(record_amount, remaining_to_remove)
                    record["amount"] = record_amount - reduction
                    remaining_to_remove -= reduction
                    if remaining_to_remove <= 0:
                        break
                self.data["emergency_fund_history"] = [
                    x for x in history
                    if self.to_float(x.get("amount", 0)) > 0
                ]

            self.save_data()
            self.show_emergency_fund()

        self.modern_button(
            buttons, "➕  Add Amount", add_amount, self.colors["green"]
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        self.modern_button(
            buttons, "✏  Edit Fund", edit_fund, self.colors["blue"]
        ).pack(side="left", expand=True, fill="x", padx=6)

        self.modern_button(
            buttons, "🗑  Delete Fund", self.delete_emergency_fund,
            self.colors["red"]
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

        progress_panel = self.panel(self.content, "📊  Emergency Fund Progress")
        progress_panel.pack(fill="x", pady=5)

        tk.Label(
            progress_panel,
            text=(
                f"{self.money(saved)} saved of {self.money(target)}"
                f"  •  {percent:.1f}% complete"
            ),
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["card"], fg=self.colors["text"]
        ).pack(anchor="w", padx=20, pady=(0, 10))

        track = tk.Frame(
            progress_panel, bg=self.colors["input"], height=14
        )
        track.pack(fill="x", padx=20, pady=(0, 18))
        track.pack_propagate(False)

        tk.Frame(
            track, bg=self.colors["green"]
        ).place(
            relx=0, rely=0, relheight=1,
            relwidth=max(0.01, percent / 100)
        )

        history_panel = self.panel(
            self.content, "🧾  Emergency Fund Amount History"
        )
        history_panel.pack(fill="both", expand=True, pady=8)

        history = list(
            reversed(self.data.get("emergency_fund_history", []))
        )

        if not history:
            tk.Label(
                history_panel,
                text="No emergency-fund amounts added yet.",
                font=("Segoe UI", 10),
                bg=self.colors["card"], fg=self.colors["muted"]
            ).pack(pady=20)
        else:
            for record in history:
                row = tk.Frame(
                    history_panel, bg=self.colors["card"],
                    highlightbackground=self.colors["border"],
                    highlightthickness=1
                )
                row.pack(fill="x", padx=15, pady=5)

                tk.Label(
                    row, text="🛡",
                    font=("Segoe UI", 15),
                    bg=self.colors["card"], fg=self.colors["green"]
                ).pack(side="left", padx=12, pady=8)

                info = tk.Frame(row, bg=self.colors["card"])
                info.pack(side="left", fill="x", expand=True, pady=7)

                tk.Label(
                    info,
                    text=f"Emergency Fund • {record.get('date', '')}",
                    font=("Segoe UI", 10, "bold"),
                    bg=self.colors["card"], fg=self.colors["text"]
                ).pack(anchor="w")

                tk.Label(
                    info,
                    text=f"Added {self.money(record.get('amount', 0))}",
                    font=("Segoe UI", 9),
                    bg=self.colors["card"], fg=self.colors["muted"]
                ).pack(anchor="w")

                tk.Button(
                    row, text="✏",
                    command=lambda rid=record.get("id"):
                        self.edit_emergency_entry(rid),
                    font=("Segoe UI", 9, "bold"),
                    fg="white", bg=self.colors["blue"],
                    activebackground=self.colors["hover"],
                    activeforeground="white", relief="flat", bd=0,
                    cursor="hand2", padx=9, pady=5
                ).pack(side="right", padx=4)

                tk.Button(
                    row, text="🗑",
                    command=lambda rid=record.get("id"):
                        self.delete_emergency_entry(rid),
                    font=("Segoe UI", 9, "bold"),
                    fg="white", bg=self.colors["red"],
                    activebackground=self.colors["hover"],
                    activeforeground="white", relief="flat", bd=0,
                    cursor="hand2", padx=9, pady=5
                ).pack(side="right", padx=4)

        tk.Label(
            progress_panel,
            text=(
                "Use Add Amount for new deposits. Edit Fund changes the "
                "overall target/saved amount, while each history row can "
                "also be edited or deleted."
            ),
            font=("Segoe UI", 9),
            bg=self.colors["card"], fg=self.colors["muted"]
        ).pack(anchor="w", padx=20, pady=(0, 18))

    def edit_emergency_entry(self, record_id):
        record = next(
            (
                x for x in self.data.get("emergency_fund_history", [])
                if x.get("id") == record_id
            ),
            None
        )
        if not record:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Emergency Fund Amount")
        dialog.geometry("430x260")
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors["bg"])
        dialog.transient(self.root)
        dialog.grab_set()

        panel = tk.Frame(
            dialog, bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        panel.pack(fill="both", expand=True, padx=18, pady=18)

        tk.Label(
            panel, text="✏  Edit Emergency Fund Amount",
            font=("Segoe UI", 15, "bold"),
            bg=self.colors["card"], fg=self.colors["text"]
        ).pack(anchor="w", padx=18, pady=(18, 12))

        amount_entry = self.dialog_entry(
            panel, "Amount (₹)", str(record.get("amount", 0))
        )

        def save_entry():
            try:
                new_amount = float(amount_entry.get().strip())
                if new_amount <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Invalid Amount",
                    "Enter a valid amount greater than 0.",
                    parent=dialog
                )
                return

            old_amount = self.to_float(record.get("amount", 0))
            new_saved = self.emergency_saved_total() - old_amount + new_amount
            target = self.emergency_target_total()

            if target > 0 and new_saved > target:
                messagebox.showerror(
                    "Target Exceeded",
                    "The edited amount would exceed the Emergency Fund target.",
                    parent=dialog
                )
                return

            record["amount"] = new_amount
            self.data["emergency_fund"]["saved"] = new_saved
            self.data["emergency_fund"]["updated_date"] = (
                datetime.now().strftime("%Y-%m-%d")
            )
            self.save_data()
            dialog.destroy()
            self.show_emergency_fund()

        self.modern_button(
            panel, "✓  Save Amount", save_entry, self.colors["blue"]
        ).pack(fill="x", padx=18, pady=18)

    def delete_emergency_entry(self, record_id):
        record = next(
            (
                x for x in self.data.get("emergency_fund_history", [])
                if x.get("id") == record_id
            ),
            None
        )
        if not record:
            return

        if not messagebox.askyesno(
            "Delete Amount",
            f"Delete emergency-fund amount {self.money(record.get('amount', 0))}?"
        ):
            return

        amount = self.to_float(record.get("amount", 0))
        self.data["emergency_fund_history"] = [
            x for x in self.data.get("emergency_fund_history", [])
            if x.get("id") != record_id
        ]

        current_saved = self.emergency_saved_total()
        self.data["emergency_fund"]["saved"] = max(
            current_saved - amount, 0
        )
        self.data["emergency_fund"]["updated_date"] = (
            datetime.now().strftime("%Y-%m-%d")
        )

        self.save_data()
        self.show_emergency_fund()

    def delete_emergency_fund(self):
        if not messagebox.askyesno(
            "Delete Emergency Fund",
            "Delete the entire Emergency Fund and all its saved amounts?"
        ):
            return

        self.data["emergency_fund"] = {
            "target": 0.0,
            "saved": 0.0,
            "updated_date": ""
        }
        self.data["emergency_fund_history"] = []
        self.save_data()
        self.show_emergency_fund()

    # ========================================================
    # ANALYTICS
    # ========================================================

    def show_analytics(self):
        self.title_label.config(text="Analytics & Insights")
        self.clear_content()

        stats = tk.Frame(self.content, bg=self.colors["bg"])
        stats.pack(fill="x", pady=5)

        # Analytics summary cards
        goal_saved = self.historical_goal_saved_total()
        goal_target = self.goal_target_total()
        emergency_saved = self.emergency_saved_total()
        emergency_target = self.emergency_target_total()

        goal_pct = (goal_saved / goal_target * 100) if goal_target > 0 else 0
        emergency_pct = (emergency_saved / emergency_target * 100) if emergency_target > 0 else 0

        values = [
            ("📈", "Savings Rate", f"{self.savings_rate():.1f}%", self.colors["green"]),
            ("🔥", "Avg. Expense", self.average_expense(), self.colors["orange"]),
            ("🏆", "Top Category", self.top_category(), self.colors["red"]),
            ("🧾", "Transactions", len(self.data["transactions"]), self.colors["primary"]),
            ("🎯", "Goals", f"{self.money(goal_saved)} / {self.money(goal_target)}", self.colors["orange"]),
            ("🛡", "Emergency Fund", f"{self.money(emergency_saved)} / {self.money(emergency_target)}", self.colors["green"])
        ]

        for i, (icon, title, value, color) in enumerate(values):
            card = self.text_stat_card(stats, icon, title, value, color)
            card.grid(row=0, column=i, sticky="nsew", padx=4)
            stats.columnconfigure(i, weight=1)

        # Make the Analytics summary cards slightly more compact when
        # six cards are displayed in one row.
        for child in stats.winfo_children():
            for label in child.winfo_children():
                if isinstance(label, tk.Label) and label.cget("text"):
                    current_font = label.cget("font")
                    if isinstance(current_font, tuple) and len(current_font) >= 2:
                        if str(label.cget("text")).startswith(("🎯", "🛡")):
                            label.configure(font=("Segoe UI", 8, "bold"))

        body = tk.Frame(self.content, bg=self.colors["bg"])
        body.pack(fill="both", expand=True, pady=12)

        category_panel = self.panel(body, "📊  Category Breakdown")
        category_panel.pack(side="left", fill="both", expand=True, padx=(0, 7))

        # Include regular expenses + Goals + Emergency Fund in Analytics.
        # This keeps the analytics view consistent with the Dashboard's
        # spending overview.
        totals = self.category_totals()
        goal_saved = self.historical_goal_saved_total()
        emergency_saved = self.emergency_saved_total()

        if goal_saved > 0:
            totals["🎯 Goals Saved"] = goal_saved
        if emergency_saved > 0:
            totals["🛡 Emergency Fund"] = emergency_saved

        if not totals:
            self.empty_message(category_panel, "No financial data", "Add expenses, goals or emergency-fund savings to see analytics.")
        else:
            total = sum(totals.values()) or 1

            for category, amount in sorted(totals.items(), key=lambda x: x[1], reverse=True):
                row = tk.Frame(category_panel, bg=self.colors["card"])
                row.pack(fill="x", padx=20, pady=5)

                pct = amount / total * 100 if total else 0

                if category == "🎯 Goals Saved":
                    icon = "🎯"
                    display_name = "Goals Saved"
                elif category == "🛡 Emergency Fund":
                    icon = "🛡"
                    display_name = "Emergency Fund"
                else:
                    icon = ICONS.get(category, "📦")
                    display_name = category

                top = tk.Frame(row, bg=self.colors["card"])
                top.pack(fill="x")

                tk.Label(
                    top,
                    text=f"{icon}  {display_name}",
                    font=("Segoe UI", 9, "bold"),
                    bg=self.colors["card"], fg=self.colors["text"]
                ).pack(side="left")

                tk.Label(
                    top,
                    text=f"{self.money(amount)}  ({pct:.1f}%)",
                    font=("Segoe UI", 9, "bold"),
                    bg=self.colors["card"], fg=self.colors["muted"]
                ).pack(side="right")

                track = tk.Frame(row, bg=self.colors["border"], height=6)
                track.pack(fill="x", pady=(4, 2))
                track.pack_propagate(False)

                if category == "🎯 Goals Saved":
                    bar_color = self.colors["orange"]
                elif category == "🛡 Emergency Fund":
                    bar_color = self.colors["green"]
                else:
                    bar_color = self.colors["primary"]

                tk.Frame(
                    track,
                    bg=bar_color
                ).place(
                    relx=0, rely=0, relheight=1,
                    relwidth=max(0.01, min(1, pct / 100))
                )

            # Dedicated progress summaries for Goals and Emergency Fund.
            progress_box = tk.Frame(category_panel, bg=self.colors["input"])
            progress_box.pack(fill="x", padx=20, pady=(12, 8))

            tk.Label(
                progress_box,
                text="🎯 Goals Progress",
                font=("Segoe UI", 9, "bold"),
                bg=self.colors["input"], fg=self.colors["text"]
            ).pack(anchor="w", padx=12, pady=(10, 2))

            tk.Label(
                progress_box,
                text=f"{self.money(goal_saved)} saved of {self.money(goal_target)}  •  {min(max(goal_pct, 0), 100):.1f}%",
                font=("Segoe UI", 9),
                bg=self.colors["input"], fg=self.colors["muted"]
            ).pack(anchor="w", padx=12)

            goal_track = tk.Frame(progress_box, bg=self.colors["border"], height=7)
            goal_track.pack(fill="x", padx=12, pady=(5, 9))
            goal_track.pack_propagate(False)
            tk.Frame(
                goal_track, bg=self.colors["orange"]
            ).place(relx=0, rely=0, relheight=1,
                    relwidth=max(0.01, min(1, goal_pct / 100)))

            tk.Label(
                progress_box,
                text="🛡 Emergency Fund Progress",
                font=("Segoe UI", 9, "bold"),
                bg=self.colors["input"], fg=self.colors["text"]
            ).pack(anchor="w", padx=12, pady=(3, 2))

            tk.Label(
                progress_box,
                text=f"{self.money(emergency_saved)} saved of {self.money(emergency_target)}  •  {min(max(emergency_pct, 0), 100):.1f}%",
                font=("Segoe UI", 9),
                bg=self.colors["input"], fg=self.colors["muted"]
            ).pack(anchor="w", padx=12)

            emergency_track = tk.Frame(progress_box, bg=self.colors["border"], height=7)
            emergency_track.pack(fill="x", padx=12, pady=(5, 12))
            emergency_track.pack_propagate(False)
            tk.Frame(
                emergency_track, bg=self.colors["green"]
            ).place(relx=0, rely=0, relheight=1,
                    relwidth=max(0.01, min(1, emergency_pct / 100)))

        trends = self.panel(body, "💡  Financial Insights")
        trends.pack(side="left", fill="both", expand=True, padx=(7, 0))
        self.analytics_insights(trends)

    def text_stat_card(self, parent, icon, title, value, color):
        card = tk.Frame(
            parent, bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )

        tk.Label(
            card, text=f"{icon}  {title}",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["card"], fg=self.colors["muted"]
        ).pack(anchor="w", padx=18, pady=(15, 4))

        tk.Label(
            card, text=str(value),
            font=("Segoe UI", 18, "bold"),
            bg=self.colors["card"], fg=color
        ).pack(anchor="w", padx=18, pady=(0, 15))

        return card

    def average_expense(self):
        expenses = [
            self.to_float(x.get("amount"))
            for x in self.data["transactions"]
            if x.get("type") == "Expense"
        ]
        return self.money(sum(expenses) / len(expenses)) if expenses else "₹0.00"

    def top_category(self):
        totals = self.category_totals()
        return max(totals, key=totals.get) if totals else "None"

    def analytics_insights(self, parent):
        totals = self.category_totals()
        lines = []

        if totals:
            top = max(totals, key=totals.get)
            lines.append(f"• Your highest spending category is {top}.")
        else:
            lines.append("• Add expenses to generate category insights.")

        rate = self.savings_rate()
        if rate >= 30:
            lines.append("• Excellent savings performance.")
        elif rate >= 15:
            lines.append("• Your savings level is healthy. Keep it consistent.")
        else:
            lines.append("• Try reducing non-essential purchases to improve savings.")

        if self.data["budgets"]:
            exceeded = []
            current = self.current_month_category_totals()
            for cat, limit in self.data["budgets"].items():
                if current.get(cat, 0) > self.to_float(limit):
                    exceeded.append(cat)
            if exceeded:
                lines.append("• Budget exceeded: " + ", ".join(exceeded) + ".")

        if self.balance() < 0:
            lines.append("• Warning: your recorded expenses are above income.")

        for line in lines:
            tk.Label(
                parent, text=line,
                font=("Segoe UI", 10),
                wraplength=450,
                justify="left",
                bg=self.colors["card"], fg=self.colors["text"]
            ).pack(anchor="w", padx=20, pady=7)

    # ========================================================
    # ADD / DELETE / EDIT DATA
    # ========================================================

    def add_salary(self):
        company = self.salary_company.get().strip()
        amount_text = self.salary_amount.get().strip()
        date = self.salary_date.get().strip()

        if not company:
            messagebox.showerror("Invalid Salary", "Enter company/source.")
            return

        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Salary", "Enter a valid positive amount.")
            return

        if not self.valid_date(date):
            messagebox.showerror("Invalid Date", "Use YYYY-MM-DD format.")
            return

        self.data["salary"].append({
            "id": datetime.now().timestamp(),
            "company": company,
            "amount": amount,
            "date": date
        })

        self.save_data()
        messagebox.showinfo("Success", "Salary added successfully! 💼")
        self.show_salary()

    def add_transaction(self):
        description = self.transaction_description.get().strip()
        amount_text = self.transaction_amount.get().strip()
        date = self.transaction_date.get().strip()

        if not description:
            messagebox.showerror("Invalid Transaction", "Enter a description.")
            return

        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Amount", "Enter a valid positive amount.")
            return

        if not self.valid_date(date):
            messagebox.showerror("Invalid Date", "Use YYYY-MM-DD format.")
            return

        self.data["transactions"].append({
            "id": datetime.now().timestamp(),
            "description": description,
            "amount": amount,
            "type": self.transaction_type.get(),
            "category": self.transaction_category.get(),
            "date": date
        })

        self.save_data()
        messagebox.showinfo("Success", "Transaction saved successfully! ✓")
        self.show_transactions()

    def edit_salary(self, salary_id):
        item = next(
            (x for x in self.data["salary"] if x.get("id") == salary_id),
            None
        )
        if not item:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Salary")
        dialog.geometry("500x390")
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors["bg"])
        dialog.transient(self.root)
        dialog.grab_set()

        panel = tk.Frame(
            dialog, bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        panel.pack(fill="both", expand=True, padx=18, pady=18)

        tk.Label(
            panel, text="✏  Edit Salary",
            font=("Segoe UI", 18, "bold"),
            bg=self.colors["card"], fg=self.colors["text"]
        ).pack(anchor="w", padx=20, pady=(20, 15))

        company_entry = self.dialog_entry(
            panel, "Company / Source", item.get("company", "")
        )
        amount_entry = self.dialog_entry(
            panel, "Salary Amount (₹)", str(item.get("amount", ""))
        )
        date_entry = self.dialog_entry(
            panel, "Salary Date (YYYY-MM-DD)", item.get("date", "")
        )

        def save_edit():
            company = company_entry.get().strip()
            date = date_entry.get().strip()
            try:
                amount = float(amount_entry.get().strip())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Invalid Salary",
                    "Enter a valid positive salary amount.",
                    parent=dialog
                )
                return

            if not company or not self.valid_date(date):
                messagebox.showerror(
                    "Invalid Salary",
                    "Enter a company/source and valid YYYY-MM-DD date.",
                    parent=dialog
                )
                return

            item["company"] = company
            item["amount"] = amount
            item["date"] = date
            self.save_data()
            dialog.destroy()
            self.show_salary()

        self.modern_button(
            panel, "✓  Save Changes", save_edit, self.colors["blue"]
        ).pack(fill="x", padx=20, pady=18)

    def delete_salary(self, salary_id):
        if not messagebox.askyesno(
            "Delete Salary",
            "Are you sure you want to delete this salary record?"
        ):
            return

        self.data["salary"] = [
            x for x in self.data["salary"]
            if x.get("id") != salary_id
        ]
        self.save_data()
        self.show_salary()

    def delete_transaction(self, transaction_id):
        if not messagebox.askyesno(
            "Delete Transaction",
            "Delete this transaction? This cannot be undone."
        ):
            return

        self.data["transactions"] = [
            x for x in self.data["transactions"]
            if x.get("id") != transaction_id
        ]
        self.save_data()
        self.refresh_transactions()

    def edit_transaction(self, transaction_id):
        item = next(
            (x for x in self.data["transactions"]
             if x.get("id") == transaction_id),
            None
        )
        if not item:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Transaction")
        dialog.geometry("520x470")
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors["bg"])
        dialog.transient(self.root)
        dialog.grab_set()

        panel = tk.Frame(
            dialog, bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        panel.pack(fill="both", expand=True, padx=18, pady=18)

        tk.Label(
            panel, text="✏  Edit Transaction",
            font=("Segoe UI", 18, "bold"),
            bg=self.colors["card"], fg=self.colors["text"]
        ).pack(anchor="w", padx=20, pady=(20, 15))

        fields = {}

        fields["description"] = self.dialog_entry(
            panel, "Description", item.get("description", "")
        )
        fields["amount"] = self.dialog_entry(
            panel, "Amount (₹)", str(item.get("amount", ""))
        )

        tk.Label(
            panel, text="Type",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["card"], fg=self.colors["muted"]
        ).pack(anchor="w", padx=20)

        type_var = tk.StringVar(value=item.get("type", "Expense"))
        ttk.Combobox(
            panel, textvariable=type_var,
            values=["Expense", "Income"], state="readonly"
        ).pack(fill="x", padx=20, pady=(4, 10), ipady=6)

        tk.Label(
            panel, text="Category",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["card"], fg=self.colors["muted"]
        ).pack(anchor="w", padx=20)

        cat_var = tk.StringVar(value=item.get("category", "Other"))
        ttk.Combobox(
            panel, textvariable=cat_var,
            values=CATEGORIES, state="readonly"
        ).pack(fill="x", padx=20, pady=(4, 10), ipady=6)

        fields["date"] = self.dialog_entry(
            panel, "Date (YYYY-MM-DD)", item.get("date", "")
        )

        def save_edit():
            description = fields["description"].get().strip()
            date = fields["date"].get().strip()

            try:
                amount = float(fields["amount"].get().strip())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Enter a valid positive amount.", parent=dialog)
                return

            if not description or not self.valid_date(date):
                messagebox.showerror(
                    "Error",
                    "Enter a description and valid YYYY-MM-DD date.",
                    parent=dialog
                )
                return

            item["description"] = description
            item["amount"] = amount
            item["type"] = type_var.get()
            item["category"] = cat_var.get()
            item["date"] = date

            self.save_data()
            dialog.destroy()
            self.show_transactions()

        self.modern_button(
            panel, "✓  Save Changes", save_edit, self.colors["primary"]
        ).pack(fill="x", padx=20, pady=18)

    # ========================================================
    # ROWS
    # ========================================================

    def salary_row(self, parent, item):
        row = tk.Frame(
            parent, bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        row.pack(fill="x", padx=20, pady=5)

        tk.Label(
            row, text="💼", font=("Segoe UI", 15),
            bg=self.colors["input"], fg=self.colors["text"],
            width=3, pady=5
        ).pack(side="left")

        info = tk.Frame(row, bg=self.colors["card"])
        info.pack(side="left", padx=12)

        tk.Label(
            info, text=item.get("company", "Unknown"),
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["card"], fg=self.colors["text"]
        ).pack(anchor="w")

        tk.Label(
            info, text=f"Salary • {item.get('date', '')}",
            font=("Segoe UI", 8),
            bg=self.colors["card"], fg=self.colors["muted"]
        ).pack(anchor="w")

        tk.Button(
            row, text="🗑",
            command=lambda sid=item.get("id"): self.delete_salary(sid),
            font=("Segoe UI", 10, "bold"),
            fg="white", bg=self.colors["red"],
            activebackground=self.colors["hover"],
            activeforeground="white",
            relief="flat", bd=0, cursor="hand2",
            padx=9, pady=5
        ).pack(side="right", padx=8, pady=8)

        tk.Label(
            row, text=f"+{self.money(item.get('amount', 0))}",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["card"], fg=self.colors["green"]
        ).pack(side="right", padx=8)

    def transaction_row(self, parent, item):
        row = tk.Frame(
            parent, bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        row.pack(fill="x", pady=4)

        tk.Label(
            row,
            text=ICONS.get(item.get("category"), "📦"),
            font=("Segoe UI", 14),
            bg=self.colors["input"],
            fg=self.colors["text"],
            width=3, pady=5
        ).pack(side="left", padx=(0, 2))

        info = tk.Frame(row, bg=self.colors["card"])
        info.pack(side="left", padx=10)

        tk.Label(
            info, text=item.get("description", "Transaction")[:45],
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["card"], fg=self.colors["text"]
        ).pack(anchor="w")

        tk.Label(
            info,
            text=f"{item.get('category', 'Other')} • {item.get('date', '')} • {item.get('type', '')}",
            font=("Segoe UI", 8),
            bg=self.colors["card"], fg=self.colors["muted"]
        ).pack(anchor="w")

        if item.get("type") == "Income":
            sign, color = "+", self.colors["green"]
        else:
            sign, color = "-", self.colors["red"]

        actions = tk.Frame(row, bg=self.colors["card"])
        actions.pack(side="right", padx=8)

        tk.Button(
            actions, text="✏",
            command=lambda tid=item.get("id"): self.edit_transaction(tid),
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["blue"], bg=self.colors["card"],
            activeforeground="white", activebackground=self.colors["blue"],
            relief="flat", bd=0, cursor="hand2", padx=7, pady=5
        ).pack(side="left")

        tk.Button(
            actions, text="🗑",
            command=lambda tid=item.get("id"): self.delete_transaction(tid),
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["red"], bg=self.colors["card"],
            activeforeground="white", activebackground=self.colors["red"],
            relief="flat", bd=0, cursor="hand2", padx=7, pady=5
        ).pack(side="left")

        tk.Label(
            row,
            text=f"{sign}{self.money(item.get('amount', 0))}",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["card"], fg=color
        ).pack(side="right", padx=5)

    # ========================================================
    # HELPERS
    # ========================================================

    def input_box(self, parent, label, column, row=0):
        frame = tk.Frame(parent, bg=self.colors["card"])
        frame.grid(row=row, column=column, sticky="ew", padx=5, pady=4)

        self.form_label(frame, label, 0, 0, pack_mode=True)

        entry = tk.Entry(
            frame,
            font=("Segoe UI", 10),
            bg=self.colors["input"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat"
        )
        entry.pack(fill="x", pady=5, ipady=8)
        return entry

    def form_label(self, parent, text, column=0, row=0, pack_mode=False):
        label = tk.Label(
            parent, text=text,
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["card"], fg=self.colors["muted"]
        )
        if pack_mode:
            label.pack(anchor="w")
        else:
            label.grid(row=row, column=column, sticky="w", padx=5, pady=(4, 2))
        return label

    def small_entry(self, parent, placeholder, column):
        frame = tk.Frame(parent, bg=self.colors["card"])
        frame.grid(row=0, column=column, sticky="ew", padx=5)

        tk.Label(
            frame, text=placeholder,
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["card"], fg=self.colors["muted"]
        ).pack(anchor="w")

        entry = tk.Entry(
            frame,
            font=("Segoe UI", 10),
            bg=self.colors["input"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat"
        )
        entry.pack(fill="x", pady=5, ipady=8)
        return entry

    def dialog_entry(self, parent, label, value):
        tk.Label(
            parent, text=label,
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["card"], fg=self.colors["muted"]
        ).pack(anchor="w", padx=20)

        entry = tk.Entry(
            parent,
            font=("Segoe UI", 10),
            bg=self.colors["input"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat"
        )
        entry.insert(0, value)
        entry.pack(fill="x", padx=20, pady=(4, 10), ipady=7)
        return entry

    def modern_button(self, parent, text, command, color):
        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 9, "bold"),
            fg="white",
            bg=color,
            activebackground=self.colors["hover"],
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=16,
            pady=9
        )
        button.bind(
            "<Enter>",
            lambda e: button.configure(bg=self.colors["hover"])
        )
        button.bind(
            "<Leave>",
            lambda e: button.configure(bg=color)
        )
        return button

    def empty_message(self, parent, title, subtitle):
        box = tk.Frame(parent, bg=self.colors["card"])
        box.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(
            box, text="📭",
            font=("Segoe UI", 30),
            bg=self.colors["card"], fg=self.colors["muted"]
        ).pack(pady=(20, 4))

        tk.Label(
            box, text=title,
            font=("Segoe UI", 13, "bold"),
            bg=self.colors["card"], fg=self.colors["text"]
        ).pack()

        tk.Label(
            box, text=subtitle,
            font=("Segoe UI", 9),
            bg=self.colors["card"], fg=self.colors["muted"]
        ).pack(pady=4)

    def clear_content(self):
        if hasattr(self, "content"):
            for widget in self.content.winfo_children():
                widget.destroy()

    def money(self, amount):
        return "₹{:,.2f}".format(self.to_float(amount))

    def valid_date(self, date_text):
        try:
            datetime.strptime(date_text, "%Y-%m-%d")
            return True
        except (ValueError, TypeError):
            return False

    def date_matches_month(self, date_string, year, month):
        try:
            value = datetime.strptime(date_string, "%Y-%m-%d").date()
            return value.year == year and value.month == month
        except (ValueError, TypeError):
            return False

    def is_same_date(self, date_string, target_date):
        try:
            value = datetime.strptime(date_string, "%Y-%m-%d").date()
            return value == target_date
        except (ValueError, TypeError):
            return False

    def is_this_month(self, date_string):
        today = datetime.now().date()
        return self.date_matches_month(date_string, today.year, today.month)

    def is_last_month(self, date_string):
        today = datetime.now().date()
        if today.month == 1:
            month, year = 12, today.year - 1
        else:
            month, year = today.month - 1, today.year
        return self.date_matches_month(date_string, year, month)

    # ========================================================
    # THEME
    # ========================================================

    def change_theme(self, event=None):
        self.theme_name = self.theme_var.get()
        self.colors = dict(THEMES[self.theme_name])
        if self.dark_mode:
            self.apply_dark_colors()
        self.build_ui()

    def toggle_mode(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.apply_dark_colors()
        else:
            self.colors = dict(THEMES[self.theme_name])
        self.build_ui()

    def apply_dark_colors(self):
        self.colors = dict(THEMES[self.theme_name])
        self.colors.update({
            "bg": "#0D0F17",
            "card": "#181B27",
            "text": "#F5F5FA",
            "muted": "#969AAC",
            "input": "#232633",
            "border": "#2C2F3C",
            "sidebar": "#090A10",
            "sidebar_hover": "#202330"
        })


if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseFlow(root)
    root.mainloop()