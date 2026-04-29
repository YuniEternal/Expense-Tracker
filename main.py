import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

DATA_FILE = "expenses.json"

class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker — Личные финансы")
        self.root.geometry("900x600")

        self.expenses = []
        self.load_data()

        # Поля ввода
        input_frame = ttk.LabelFrame(root, text="Добавить расход", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(input_frame, text="Сумма:").grid(row=0, column=0, padx=5, pady=5)
        self.amount_entry = ttk.Entry(input_frame, width=15)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Категория:").grid(row=0, column=2, padx=5, pady=5)
        self.category_var = tk.StringVar()
        categories = ["Еда", "Транспорт", "Развлечения", "Здоровье", "Другое"]
        self.category_combo = ttk.Combobox(input_frame, textvariable=self.category_var, values=categories, width=15)
        self.category_combo.grid(row=0, column=3, padx=5, pady=5)
        self.category_combo.current(0)

        ttk.Label(input_frame, text="Дата (ГГГГ-ММ-ДД):").grid(row=0, column=4, padx=5, pady=5)
        self.date_entry = ttk.Entry(input_frame, width=15)
        self.date_entry.grid(row=0, column=5, padx=5, pady=5)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        self.add_btn = ttk.Button(input_frame, text="➕ Добавить расход", command=self.add_expense)
        self.add_btn.grid(row=0, column=6, padx=10, pady=5)

        # Фильтры
        filter_frame = ttk.LabelFrame(root, text="Фильтрация", padding=10)
        filter_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(filter_frame, text="Категория:").grid(row=0, column=0, padx=5)
        self.filter_category_var = tk.StringVar()
        self.filter_category_combo = ttk.Combobox(filter_frame, textvariable=self.filter_category_var,
                                                  values=["Все"] + categories, width=15)
        self.filter_category_combo.grid(row=0, column=1, padx=5)
        self.filter_category_combo.current(0)

        ttk.Label(filter_frame, text="Дата от (ГГГГ-ММ-ДД):").grid(row=0, column=2, padx=5)
        self.filter_date_from = ttk.Entry(filter_frame, width=12)
        self.filter_date_from.grid(row=0, column=3, padx=5)

        ttk.Label(filter_frame, text="до:").grid(row=0, column=4, padx=5)
        self.filter_date_to = ttk.Entry(filter_frame, width=12)
        self.filter_date_to.grid(row=0, column=5, padx=5)

        self.filter_btn = ttk.Button(filter_frame, text="🔍 Применить фильтр", command=self.apply_filter)
        self.filter_btn.grid(row=0, column=6, padx=10)
        self.reset_filter_btn = ttk.Button(filter_frame, text="❌ Сбросить", command=self.reset_filter)
        self.reset_filter_btn.grid(row=0, column=7, padx=5)

        # Таблица расходов
        columns = ("ID", "Дата", "Категория", "Сумма")
        self.tree = ttk.Treeview(root, columns=columns, show="headings", height=15)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        # Итоговая сумма за период
        summary_frame = ttk.Frame(root)
        summary_frame.pack(fill="x", padx=10, pady=5)
        self.summary_label = ttk.Label(summary_frame, text="💰 Сумма за период: 0.00", font=("Arial", 12, "bold"))
        self.summary_label.pack(side="left")

        # Кнопка удаления
        self.delete_btn = ttk.Button(root, text="🗑 Удалить выбранное", command=self.delete_selected)
        self.delete_btn.pack(pady=5)

        self.update_table()
        self.calculate_total()

 
    def validate_amount(self, amount_str):
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
            return amount
        except ValueError:
            messagebox.showerror("Ошибка", "Сумма должна быть положительным числом!")
            return None

    def validate_date(self, date_str):
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты! Используйте ГГГГ-ММ-ДД (например, 2025-03-30)")
            return False


    def add_expense(self):
        amount_val = self.validate_amount(self.amount_entry.get())
        if amount_val is None:
            return
        category = self.category_var.get().strip()
        if not category:
            messagebox.showerror("Ошибка", "Выберите категорию!")
            return
        date_str = self.date_entry.get().strip()
        if not self.validate_date(date_str):
            return

        new_id = max([e["id"] for e in self.expenses], default=0) + 1
        self.expenses.append({
            "id": new_id,
            "amount": amount_val,
            "category": category,
            "date": date_str
        })
        self.save_data()
        self.update_table()
        self.calculate_total()
        self.amount_entry.delete(0, tk.END)
        self.amount_entry.insert(0, "")
        messagebox.showinfo("Успех", "Расход добавлен!")


    def apply_filter(self):
        self.update_table()

    def reset_filter(self):
        self.filter_category_var.set("Все")
        self.filter_date_from.delete(0, tk.END)
        self.filter_date_to.delete(0, tk.END)
        self.update_table()

    def get_filtered_expenses(self):
        filtered = self.expenses.copy()
        cat = self.filter_category_var.get()
        if cat != "Все":
            filtered = [e for e in filtered if e["category"] == cat]

        date_from = self.filter_date_from.get().strip()
        date_to = self.filter_date_to.get().strip()
        if date_from:
            try:
                datetime.strptime(date_from, "%Y-%m-%d")
                filtered = [e for e in filtered if e["date"] >= date_from]
            except:
                pass
        if date_to:
            try:
                datetime.strptime(date_to, "%Y-%m-%d")
                filtered = [e for e in filtered if e["date"] <= date_to]
            except:
                pass
        return filtered

    def update_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        filtered = self.get_filtered_expenses()
        for exp in filtered:
            self.tree.insert("", "end", values=(exp["id"], exp["date"], exp["category"], f"{exp['amount']:.2f}"))
        self.calculate_total(filtered)

    def calculate_total(self, expenses_list=None):
        if expenses_list is None:
            expenses_list = self.get_filtered_expenses()
        total = sum(e["amount"] for e in expenses_list)
        self.summary_label.config(text=f"💰 Сумма за период: {total:.2f} руб.")


    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите запись для удаления!")
            return
        for item in selected:
            exp_id = int(self.tree.item(item, "values")[0])
            self.expenses = [e for e in self.expenses if e["id"] != exp_id]
        self.save_data()
        self.update_table()


    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.expenses = json.load(f)
            except:
                self.expenses = []
        else:
            self.expenses = []

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.expenses, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()
