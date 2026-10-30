import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3, os, sys, csv
from datetime import date, datetime
from pathlib import Path

APP_NAME = "College Fee Management System Pro"
SEM_GENERAL = 27000
SEM_RESERVED = 23250
FINE_AMOUNT = 100

def data_dir():
    if getattr(sys, "frozen", False):
        root = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "CollegeFeeManagementSystemPro"
    else:
        root = Path(__file__).resolve().parent
    root.mkdir(parents=True, exist_ok=True)
    return root

DB = data_dir() / "college_fees.db"

class CollegeFeeApp:
    def __init__(self, root):
        self.root = root
        root.title(APP_NAME)
        root.geometry("1280x780")
        root.minsize(1050, 680)
        root.configure(bg="#f3f6fb")
        self.conn = sqlite3.connect(DB)
        self.conn.row_factory = sqlite3.Row
        self.setup_db()
        self.style()
        self.build_ui()
        self.refresh_all()

    def setup_db(self):
        c=self.conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT, admission_no TEXT UNIQUE, name TEXT NOT NULL,
            phone TEXT, course TEXT, semester TEXT, category TEXT DEFAULT 'General',
            bus_route TEXT, bus_fee REAL DEFAULT 0, active INTEGER DEFAULT 1)""")
        c.execute("""CREATE TABLE IF NOT EXISTS charges(
            id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL,
            fee_type TEXT NOT NULL, period TEXT NOT NULL, description TEXT,
            amount REAL NOT NULL, fine REAL DEFAULT 0, created_at TEXT,
            UNIQUE(student_id, fee_type, period),
            FOREIGN KEY(student_id) REFERENCES students(id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS payments(
            id INTEGER PRIMARY KEY AUTOINCREMENT, charge_id INTEGER NOT NULL,
            amount REAL NOT NULL, fine_paid REAL DEFAULT 0, paid_on TEXT,
            method TEXT, note TEXT, FOREIGN KEY(charge_id) REFERENCES charges(id))""")
        self.conn.commit()

    def style(self):
        s=ttk.Style()
        try: s.theme_use("clam")
        except: pass
        s.configure("Treeview", rowheight=29, font=("Segoe UI",10), background="white", fieldbackground="white")
        s.configure("Treeview.Heading", font=("Segoe UI",10,"bold"), background="#e8eef8")
        s.configure("TButton", font=("Segoe UI",10), padding=7)
        s.configure("TLabel", font=("Segoe UI",10))
        s.configure("TEntry", padding=6)
        s.configure("TCombobox", padding=5)

    def build_ui(self):
        header=tk.Frame(self.root,bg="#142b4a",height=76); header.pack(fill="x")
        tk.Label(header,text="🎓  COLLEGE FEE MANAGEMENT PRO",bg="#142b4a",fg="white",font=("Segoe UI",19,"bold")).pack(side="left",padx=24,pady=18)
        tk.Label(header,text="BUS FEE  +  6-MONTH SEMESTER FEE",bg="#142b4a",fg="#c8d8ef",font=("Segoe UI",10,"bold")).pack(side="right",padx=24)
        body=tk.Frame(self.root,bg="#f3f6fb"); body.pack(fill="both",expand=True,padx=18,pady=16)
        nav=tk.Frame(body,bg="#203c60",width=205); nav.pack(side="left",fill="y"); nav.pack_propagate(False)
        self.content=tk.Frame(body,bg="#f3f6fb"); self.content.pack(side="left",fill="both",expand=True,padx=(16,0))
        self.pages={}
        for label,func in [("Dashboard",self.show_dashboard),("Students",self.show_students),("Fee Charges",self.show_charges),("Record Payment",self.show_payment),("Reports & Export",self.show_reports),("Settings",self.show_settings)]:
            tk.Button(nav,text="   "+label,anchor="w",command=func,bg="#203c60",fg="white",activebackground="#315982",activeforeground="white",relief="flat",font=("Segoe UI",11),padx=12,pady=14).pack(fill="x",padx=8,pady=3)
        tk.Label(nav,text="Local database\ncollege_fees.db",bg="#203c60",fg="#b9cbe0",font=("Segoe UI",9),justify="left").pack(side="bottom",anchor="w",padx=18,pady=18)
        self.show_dashboard()

    def clear(self):
        for w in self.content.winfo_children(): w.destroy()

    def title(self, text, sub=None):
        tk.Label(self.content,text=text,bg="#f3f6fb",fg="#142b4a",font=("Segoe UI",20,"bold")).pack(anchor="w",pady=(2,2))
        if sub: tk.Label(self.content,text=sub,bg="#f3f6fb",fg="#66758a",font=("Segoe UI",10)).pack(anchor="w",pady=(0,12))

    def card(self,parent,label,value,color="#142b4a"):
        f=tk.Frame(parent,bg="white",highlightbackground="#dce4ef",highlightthickness=1)
        tk.Label(f,text=label,bg="white",fg="#64748b",font=("Segoe UI",10,"bold")).pack(anchor="w",padx=16,pady=(13,3))
        tk.Label(f,text=str(value),bg="white",fg=color,font=("Segoe UI",21,"bold")).pack(anchor="w",padx=16,pady=(0,13))
        return f

    def totals(self):
        cur=self.conn.cursor()
        students=cur.execute("SELECT COUNT(*) n FROM students WHERE active=1").fetchone()["n"]
        charges=cur.execute("SELECT COALESCE(SUM(amount+fine),0) n FROM charges").fetchone()["n"]
        paid=cur.execute("SELECT COALESCE(SUM(amount+fine_paid),0) n FROM payments").fetchone()["n"]
        pending=max(0,charges-paid)
        due_students=cur.execute("""SELECT COUNT(DISTINCT c.student_id) n FROM charges c
          LEFT JOIN (SELECT charge_id,SUM(amount+fine_paid) paid FROM payments GROUP BY charge_id) p ON p.charge_id=c.id
          WHERE c.amount+c.fine-COALESCE(p.paid,0)>0.009""").fetchone()["n"]
        bus=cur.execute("SELECT COALESCE(SUM(amount+fine),0) n FROM charges WHERE fee_type='Bus'").fetchone()["n"]
        sem=cur.execute("SELECT COALESCE(SUM(amount+fine),0) n FROM charges WHERE fee_type='Semester'").fetchone()["n"]
        return students,charges,paid,pending,due_students,bus,sem

    def show_dashboard(self):
        self.clear(); self.title("Dashboard","College fee overview — live totals from your local database")
        vals=self.totals()
        grid=tk.Frame(self.content,bg="#f3f6fb"); grid.pack(fill="x",pady=8)
        items=[("Total Students",vals[0]),("Total Fees",f"₹{vals[1]:,.0f}"),("Collected",f"₹{vals[2]:,.0f}"),("Pending Fees",f"₹{vals[3]:,.0f}"),("Pending Students",vals[4]),("Bus Fee Charges",f"₹{vals[5]:,.0f}"),("Semester Fee Charges",f"₹{vals[6]:,.0f}")]
        for i,(a,b) in enumerate(items):
            c=self.card(grid,a,b,"#c2410c" if "Pending" in a else "#142b4a")
            c.grid(row=i//4,column=i%4,sticky="nsew",padx=5,pady=5)
        for j in range(4): grid.grid_columnconfigure(j,weight=1)
        lower=tk.Frame(self.content,bg="white",highlightbackground="#dce4ef",highlightthickness=1); lower.pack(fill="both",expand=True,pady=12)
        tk.Label(lower,text="Fee collection snapshot",bg="white",fg="#142b4a",font=("Segoe UI",14,"bold")).pack(anchor="w",padx=18,pady=14)
        self.draw_bar(lower,"Bus Fee",self.conn.execute("SELECT COALESCE(SUM(p.amount+p.fine_paid),0) FROM payments p JOIN charges c ON c.id=p.charge_id WHERE c.fee_type='Bus'").fetchone()[0],
                      "Semester Fee",self.conn.execute("SELECT COALESCE(SUM(p.amount+p.fine_paid),0) FROM payments p JOIN charges c ON c.id=p.charge_id WHERE c.fee_type='Semester'").fetchone()[0])
        tk.Label(lower,text="Tip: Add students → create fee charges → record payments. Pending amounts update automatically.",bg="white",fg="#64748b",font=("Segoe UI",10)).pack(anchor="w",padx=18,pady=15)

    def draw_bar(self,parent,l1,v1,l2,v2):
        mx=max(float(v1),float(v2),1)
        for label,val in [(l1,v1),(l2,v2)]:
            row=tk.Frame(parent,bg="white"); row.pack(fill="x",padx=18,pady=8)
            tk.Label(row,text=f"{label}  ₹{val:,.0f}",bg="white",width=25,anchor="w",font=("Segoe UI",10,"bold")).pack(side="left")
            bar=tk.Canvas(row,height=18,bg="#edf2f8",highlightthickness=0); bar.pack(side="left",fill="x",expand=True)
            bar.update_idletasks(); w=max(4,int(bar.winfo_width()*float(val)/mx)); bar.create_rectangle(0,2,w,16,fill="#2c75b8",outline="")

    def make_tree(self,parent,cols,heads):
        frame=tk.Frame(parent); frame.pack(fill="both",expand=True,pady=8)
        tree=ttk.Treeview(frame,columns=cols,show="headings")
        for c,h in zip(cols,heads): tree.heading(c,text=h); tree.column(c,width=125,anchor="w")
        vs=ttk.Scrollbar(frame,orient="vertical",command=tree.yview); tree.configure(yscrollcommand=vs.set)
        tree.pack(side="left",fill="both",expand=True); vs.pack(side="right",fill="y")
        return tree

    def show_students(self):
        self.clear(); self.title("Student Management","Add and maintain student, category, semester and bus details.")
        form=tk.LabelFrame(self.content,text="Student details",bg="#f3f6fb",fg="#142b4a",font=("Segoe UI",11,"bold")); form.pack(fill="x",pady=5)
        fields=[("Admission No","admission"),("Student Name","name"),("Mobile","phone"),("Course","course"),("Current Semester","semester"),("Bus Route / Stop","route"),("Monthly Bus Fee","busfee")]
        self.stu_vars={}
        for i,(lab,key) in enumerate(fields):
            r=i//4; c=(i%4)*2
            tk.Label(form,text=lab,bg="#f3f6fb").grid(row=r,column=c,sticky="w",padx=8,pady=6)
            v=tk.StringVar(); self.stu_vars[key]=v
            e=ttk.Entry(form,textvariable=v,width=22); e.grid(row=r,column=c+1,sticky="ew",padx=5,pady=6)
        tk.Label(form,text="Category",bg="#f3f6fb").grid(row=2,column=0,sticky="w",padx=8,pady=6)
        self.cat=tk.StringVar(value="General"); ttk.Combobox(form,textvariable=self.cat,values=["General","Reserved"],state="readonly",width=19).grid(row=2,column=1,padx=5,pady=6)
        for c in range(8): form.grid_columnconfigure(c,weight=1)
        tk.Button(form,text="＋ Add Student",command=self.add_student,bg="#1769aa",fg="white",relief="flat",padx=14,pady=8).grid(row=3,column=0,columnspan=2,padx=8,pady=10,sticky="w")
        tk.Button(form,text="Delete Selected",command=self.delete_student,bg="#b42318",fg="white",relief="flat",padx=14,pady=8).grid(row=3,column=2,columnspan=2,padx=8,pady=10,sticky="w")
        self.student_tree=self.make_tree(self.content,("id","admission","name","phone","course","semester","category","bus"),("ID","Admission No","Name","Mobile","Course","Semester","Category","Bus Fee"))
        self.load_students()

    def add_student(self):
        v={k:x.get().strip() for k,x in self.stu_vars.items()}
        if not v["name"]: messagebox.showwarning("Required","Student name is required."); return
        try:
            self.conn.execute("INSERT INTO students(admission_no,name,phone,course,semester,category,bus_route,bus_fee) VALUES(?,?,?,?,?,?,?,?)",
                (v["admission"] or None,v["name"],v["phone"],v["course"],v["semester"],self.cat.get(),v["route"],float(v["busfee"] or 0)))
            self.conn.commit(); self.load_students(); self.refresh_dashboard_only()
            for x in self.stu_vars.values(): x.set("")
            messagebox.showinfo("Saved","Student added successfully.")
        except sqlite3.IntegrityError: messagebox.showerror("Duplicate","Admission number already exists.")
        except ValueError: messagebox.showerror("Invalid","Monthly bus fee must be a number.")

    def load_students(self):
        if not hasattr(self,"student_tree"): return
        self.student_tree.delete(*self.student_tree.get_children())
        for r in self.conn.execute("SELECT * FROM students WHERE active=1 ORDER BY id DESC"):
            self.student_tree.insert("","end",values=(r["id"],r["admission_no"] or "",r["name"],r["phone"],r["course"],r["semester"],r["category"],f"₹{r['bus_fee']:,.0f}"))

    def delete_student(self):
        sel=self.student_tree.selection()
        if not sel: messagebox.showwarning("Select","Select a student first."); return
        sid=self.student_tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirm","Delete this student? Existing fee history is retained."):
            self.conn.execute("UPDATE students SET active=0 WHERE id=?",(sid,)); self.conn.commit(); self.load_students(); self.refresh_dashboard_only()

    def show_charges(self):
        self.clear(); self.title("Fee Charges","Generate Bus monthly dues or Semester dues for a 6-month semester.")
        box=tk.LabelFrame(self.content,text="Create fee charges",bg="#f3f6fb",font=("Segoe UI",11,"bold")); box.pack(fill="x",pady=8)
        self.period=tk.StringVar(value=date.today().strftime("%Y-%m"))
        self.sem_label=tk.StringVar(value="Semester 1")
        tk.Label(box,text="Period (YYYY-MM)",bg="#f3f6fb").grid(row=0,column=0,padx=10,pady=10)
        ttk.Entry(box,textvariable=self.period,width=16).grid(row=0,column=1,padx=5)
        tk.Label(box,text="Semester",bg="#f3f6fb").grid(row=0,column=2,padx=10)
        ttk.Combobox(box,textvariable=self.sem_label,values=[f"Semester {i}" for i in range(1,9)],state="readonly",width=15).grid(row=0,column=3,padx=5)
        tk.Button(box,text="Generate Bus Fee (selected month)",command=self.gen_bus,bg="#1769aa",fg="white",relief="flat",padx=12,pady=8).grid(row=1,column=0,columnspan=2,padx=10,pady=10)
        tk.Button(box,text="Generate Semester Fee (6 months)",command=self.gen_sem,bg="#16794b",fg="white",relief="flat",padx=12,pady=8).grid(row=1,column=2,columnspan=2,padx=10,pady=10)
        tk.Label(box,text="Semester fee: General ₹27,000 | Reserved ₹23,250 | Late fine ₹100 after day 10 (once per student per month).",bg="#f3f6fb",fg="#53657a").grid(row=2,column=0,columnspan=4,sticky="w",padx=10,pady=5)
        self.charge_tree=self.make_tree(self.content,("id","student","type","period","amount","fine","paid","pending"),("ID","Student","Fee Type","Period","Fee","Fine","Paid","Pending"))
        self.load_charges()

    def create_charge(self,sid,typ,period,desc,amount,fine=0):
        self.conn.execute("INSERT OR IGNORE INTO charges(student_id,fee_type,period,description,amount,fine,created_at) VALUES(?,?,?,?,?,?,?)",
                          (sid,typ,period,desc,amount,fine,date.today().isoformat()))

    def fine_for_student_month(self, student_id, period):
        # One ₹100 late fine total per student per month, shared across fee types.
        if date.today().day <= 10 or period != date.today().strftime("%Y-%m"):
            return 0
        already = self.conn.execute("SELECT 1 FROM charges WHERE student_id=? AND period=? AND fine>0 LIMIT 1", (student_id, period)).fetchone()
        return 0 if already else FINE_AMOUNT

    def gen_bus(self):
        p=self.period.get().strip()
        try: datetime.strptime(p,"%Y-%m")
        except: messagebox.showerror("Period","Enter period as YYYY-MM, e.g. 2026-10."); return
        rows=self.conn.execute("SELECT * FROM students WHERE active=1 AND bus_fee>0").fetchall()
        for s in rows:
            fine=self.fine_for_student_month(s["id"],p)
            self.create_charge(s["id"],"Bus",p,"Monthly bus fee",s["bus_fee"],fine)
        self.conn.commit(); self.load_charges(); self.refresh_dashboard_only()
        messagebox.showinfo("Done",f"Bus fee charges processed for {len(rows)} students. Duplicate months are skipped.")

    def gen_sem(self):
        p=self.period.get().strip()
        try: datetime.strptime(p,"%Y-%m")
        except: messagebox.showerror("Period","Enter period as YYYY-MM, e.g. 2026-10."); return
        rows=self.conn.execute("SELECT * FROM students WHERE active=1").fetchall()
        for s in rows:
            amount=SEM_GENERAL if s["category"]=="General" else SEM_RESERVED
            fine=self.fine_for_student_month(s["id"],p)
            desc=f"{self.sem_label.get()} — 6 months"
            self.create_charge(s["id"],"Semester",p,desc,amount,fine)
        self.conn.commit(); self.load_charges(); self.refresh_dashboard_only()
        messagebox.showinfo("Done",f"Semester charges processed for {len(rows)} students. Duplicate periods are skipped.")

    def load_charges(self):
        if not hasattr(self,"charge_tree"): return
        self.charge_tree.delete(*self.charge_tree.get_children())
        rows=self.conn.execute("""SELECT c.*,s.name,COALESCE((SELECT SUM(amount+fine_paid) FROM payments WHERE charge_id=c.id),0) paid
            FROM charges c JOIN students s ON s.id=c.student_id ORDER BY c.id DESC""")
        for r in rows:
            due=max(0,r["amount"]+r["fine"]-r["paid"])
            self.charge_tree.insert("","end",values=(r["id"],r["name"],r["fee_type"],r["period"],f"₹{r['amount']:,.0f}",f"₹{r['fine']:,.0f}",f"₹{r['paid']:,.0f}",f"₹{due:,.0f}"))

    def show_payment(self):
        self.clear(); self.title("Record Payment","Record full or partial payments against an existing fee charge.")
        box=tk.LabelFrame(self.content,text="Payment entry",bg="#f3f6fb",font=("Segoe UI",11,"bold")); box.pack(fill="x",pady=8)
        rows=self.conn.execute("""SELECT c.id,s.name,c.fee_type,c.period,c.amount+c.fine-COALESCE((SELECT SUM(amount+fine_paid) FROM payments WHERE charge_id=c.id),0) due
            FROM charges c JOIN students s ON s.id=c.student_id ORDER BY c.id DESC""").fetchall()
        self.charge_map={f"#{r['id']} | {r['name']} | {r['fee_type']} | {r['period']} | Due ₹{r['due']:,.0f}":r for r in rows if r["due"]>0.009}
        self.pay_charge=tk.StringVar(value=next(iter(self.charge_map),""))
        self.pay_amount=tk.StringVar(); self.pay_method=tk.StringVar(value="Cash"); self.pay_date=tk.StringVar(value=date.today().isoformat())
        tk.Label(box,text="Select pending charge",bg="#f3f6fb").grid(row=0,column=0,padx=10,pady=10,sticky="w")
        ttk.Combobox(box,textvariable=self.pay_charge,values=list(self.charge_map),width=65,state="readonly").grid(row=0,column=1,columnspan=3,padx=5,pady=10,sticky="w")
        for i,(lab,var) in enumerate([("Amount received (₹)",self.pay_amount),("Payment date (YYYY-MM-DD)",self.pay_date)]):
            tk.Label(box,text=lab,bg="#f3f6fb").grid(row=1,column=i*2,padx=10,pady=8,sticky="w"); ttk.Entry(box,textvariable=var,width=22).grid(row=1,column=i*2+1,padx=5,pady=8)
        tk.Label(box,text="Payment method",bg="#f3f6fb").grid(row=2,column=0,padx=10,pady=8,sticky="w")
        ttk.Combobox(box,textvariable=self.pay_method,values=["Cash","UPI","Bank Transfer","Card","Cheque"],state="readonly",width=19).grid(row=2,column=1,padx=5,pady=8,sticky="w")
        tk.Button(box,text="Save Payment & Receipt",command=self.save_payment,bg="#16794b",fg="white",relief="flat",padx=14,pady=9).grid(row=2,column=2,padx=10,pady=8)
        self.payment_tree=self.make_tree(self.content,("id","student","type","date","amount","method"),("Receipt ID","Student","Fee Type","Date","Amount","Method"))
        for r in self.conn.execute("""SELECT p.*,s.name,c.fee_type FROM payments p JOIN charges c ON c.id=p.charge_id JOIN students s ON s.id=c.student_id ORDER BY p.id DESC LIMIT 100"""):
            self.payment_tree.insert("","end",values=(r["id"],r["name"],r["fee_type"],r["paid_on"],f"₹{r['amount']+r['fine_paid']:,.0f}",r["method"]))

    def save_payment(self):
        label=self.pay_charge.get()
        if label not in self.charge_map: messagebox.showwarning("Select","Select a pending charge."); return
        try:
            amount=float(self.pay_amount.get()); datetime.strptime(self.pay_date.get(),"%Y-%m-%d")
            if amount<=0: raise ValueError()
        except: messagebox.showerror("Invalid","Enter a valid positive amount and date."); return
        r=self.charge_map[label]; due=float(r["due"])
        if amount>due+0.001: messagebox.showerror("Too much",f"Maximum pending amount is ₹{due:,.2f}."); return
        self.conn.execute("INSERT INTO payments(charge_id,amount,fine_paid,paid_on,method) VALUES(?,?,?,?,?)",(r["id"],amount,0,self.pay_date.get(),self.pay_method.get()))
        self.conn.commit()
        pid=self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        self.refresh_all()
        self.make_receipt(pid)

    def make_receipt(self,pid):
        r=self.conn.execute("""SELECT p.*,s.name,s.admission_no,s.course,c.fee_type,c.period,c.description,c.amount,c.fine
          FROM payments p JOIN charges c ON c.id=p.charge_id JOIN students s ON s.id=c.student_id WHERE p.id=?""",(pid,)).fetchone()
        txt=f"""{APP_NAME}
PAYMENT RECEIPT
Receipt No: {pid}
Date: {r['paid_on']}
Student: {r['name']}
Admission No: {r['admission_no'] or '-'}
Course: {r['course'] or '-'}
Fee Type: {r['fee_type']}
Period: {r['period']}
Description: {r['description'] or '-'}
Payment Method: {r['method']}
Amount Received: Rs. {r['amount']+r['fine_paid']:,.2f}

Thank you.
"""
        path=filedialog.asksaveasfilename(defaultextension=".txt",initialfile=f"Receipt-{pid}.txt",filetypes=[("Text receipt","*.txt")])
        if path:
            with open(path,"w",encoding="utf-8") as f:f.write(txt)
            messagebox.showinfo("Receipt saved",f"Receipt saved:\n{path}")

    def show_reports(self):
        self.clear(); self.title("Reports & Export","Export student, fee charge and payment records to CSV (opens in Excel).")
        box=tk.Frame(self.content,bg="#f3f6fb"); box.pack(fill="x",pady=10)
        tk.Button(box,text="Export Students CSV",command=lambda:self.export("students"),bg="#1769aa",fg="white",relief="flat",padx=14,pady=10).pack(side="left",padx=5)
        tk.Button(box,text="Export Fee Charges CSV",command=lambda:self.export("charges"),bg="#1769aa",fg="white",relief="flat",padx=14,pady=10).pack(side="left",padx=5)
        tk.Button(box,text="Export Payments CSV",command=lambda:self.export("payments"),bg="#1769aa",fg="white",relief="flat",padx=14,pady=10).pack(side="left",padx=5)
        tk.Button(box,text="Backup Database",command=self.backup,bg="#16794b",fg="white",relief="flat",padx=14,pady=10).pack(side="left",padx=5)
        tk.Label(self.content,text="Pending fee summary",bg="#f3f6fb",fg="#142b4a",font=("Segoe UI",14,"bold")).pack(anchor="w",pady=(18,5))
        self.report_tree=self.make_tree(self.content,("student","type","period","total","paid","pending"),("Student","Fee Type","Period","Total","Paid","Pending"))
        self.load_report()

    def load_report(self):
        if not hasattr(self,"report_tree"): return
        self.report_tree.delete(*self.report_tree.get_children())
        for r in self.conn.execute("""SELECT s.name,c.fee_type,c.period,c.amount+c.fine total,
          COALESCE((SELECT SUM(amount+fine_paid) FROM payments WHERE charge_id=c.id),0) paid
          FROM charges c JOIN students s ON s.id=c.student_id ORDER BY s.name"""):
            self.report_tree.insert("","end",values=(r["name"],r["fee_type"],r["period"],f"₹{r['total']:,.0f}",f"₹{r['paid']:,.0f}",f"₹{max(0,r['total']-r['paid']):,.0f}"))

    def export(self,kind):
        queries={
          "students":"SELECT * FROM students",
          "charges":"SELECT c.*,s.name student_name FROM charges c JOIN students s ON s.id=c.student_id",
          "payments":"SELECT p.*,s.name student_name,c.fee_type,c.period FROM payments p JOIN charges c ON c.id=p.charge_id JOIN students s ON s.id=c.student_id"}
        path=filedialog.asksaveasfilename(defaultextension=".csv",initialfile=f"{kind}.csv",filetypes=[("CSV","*.csv")])
        if not path:return
        cur=self.conn.execute(queries[kind]); headers=[x[0] for x in cur.description]
        with open(path,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f); w.writerow(headers); w.writerows(cur.fetchall())
        messagebox.showinfo("Exported",f"Saved:\n{path}")

    def backup(self):
        path=filedialog.asksaveasfilename(defaultextension=".db",initialfile="college_fees_backup.db",filetypes=[("SQLite backup","*.db")])
        if path:
            dest=sqlite3.connect(path)
            self.conn.backup(dest); dest.close()
            messagebox.showinfo("Backup","Database backup created successfully.")

    def show_settings(self):
        self.clear(); self.title("Settings","Default fee rules configured for this project.")
        box=tk.Frame(self.content,bg="white",highlightbackground="#dce4ef",highlightthickness=1); box.pack(fill="x",pady=12)
        settings=[("General semester fee","₹27,000"),("Reserved semester fee","₹23,250"),("Semester duration","6 months"),("Late fine","₹100"),("Fine rule","After 10th; once per student per month"),("Database location",str(DB))]
        for a,b in settings:
            row=tk.Frame(box,bg="white"); row.pack(fill="x",padx=18,pady=12)
            tk.Label(row,text=a,bg="white",fg="#64748b",width=28,anchor="w").pack(side="left")
            tk.Label(row,text=b,bg="white",fg="#142b4a",font=("Segoe UI",10,"bold"),anchor="w").pack(side="left")
        tk.Label(self.content,text="Important: Keep regular backups. Database is stored locally on this PC; this starter version does not sync to Google Drive automatically.",bg="#f3f6fb",fg="#a33b21",wraplength=850,justify="left").pack(anchor="w",pady=12)

    def refresh_dashboard_only(self):
        if self.content.winfo_children() and hasattr(self,"student_tree"): self.load_students()
    def refresh_all(self):
        if hasattr(self,"student_tree"): self.load_students()
        if hasattr(self,"charge_tree"): self.load_charges()
        if hasattr(self,"report_tree"): self.load_report()
        if hasattr(self,"payment_tree"): self.show_payment()
        # dashboard refreshed when opened
    def on_close(self):
        self.conn.close(); self.root.destroy()

if __name__=="__main__":
    root=tk.Tk()
    app=CollegeFeeApp(root)
    root.protocol("WM_DELETE_WINDOW",app.on_close)
    root.mainloop()
