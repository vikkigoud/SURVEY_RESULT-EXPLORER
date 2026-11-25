import csv, random
from datetime import date, timedelta
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QStackedWidget, QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, QTextEdit, QDialog,
    QFormLayout, QDoubleSpinBox, QDateEdit, QMessageBox, QFileDialog, QHeaderView, QAbstractItemView,
    QScrollArea, QListWidget, QListWidgetItem, QProgressBar)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from ..core.models import SurveyRecord
from ..core.validation import validate_record, ValidationError
from ..core.analytics import summarize, insights
from ..core.cleaning import clean_records
from ..core.search import filter_records
from ..core.export import export_records, export_summary


NAVY = "#142238"; NAVY2 = "#1D304C"; BLUE = "#5B8DEF"; TEAL = "#21B7A5"; BG = "#F4F7FB"; TEXT = "#1D2939"; MUTED = "#728197"


class RecordDialog(QDialog):
    def __init__(self, parent=None, record=None):
        super().__init__(parent); self.record = record
        self.setWindowTitle("Edit response" if record else "Add response")
        self.setMinimumWidth(430); self.setStyleSheet("QDialog{background:#f5f7fb;} QLabel{color:#24344a;} QLineEdit,QComboBox,QTextEdit,QDateEdit{background:white;border:1px solid #d7dfeb;border-radius:8px;padding:8px;color:#17253a;} QPushButton{background:#527fe5;color:white;border:0;border-radius:8px;padding:10px 18px;font-weight:600;} QPushButton#cancel{background:#e4eaf2;color:#24344a;}")
        form = QFormLayout(self); form.setSpacing(12)
        self.respondent = QLineEdit(record.respondent if record else ""); self.respondent.setPlaceholderText("e.g. Student 001")
        self.category = QComboBox(); self.category.setEditable(True); self.category.addItems(["Academics", "Campus Facilities", "Student Services", "Technology", "Events", "Food", "Other"])
        if record: self.category.setCurrentText(record.category)
        self.rating = QDoubleSpinBox(); self.rating.setRange(0,100); self.rating.setDecimals(1); self.rating.setSuffix(" / 100"); self.rating.setValue(float(record.rating) if record else 75)
        self.date = QDateEdit(); self.date.setCalendarPopup(True); self.date.setDisplayFormat("yyyy-MM-dd"); self.date.setDate(date.fromisoformat(record.response_date) if record else date.today())
        self.comments = QTextEdit(); self.comments.setMaximumHeight(90); self.comments.setPlaceholderText("Optional notes..."); self.comments.setPlainText(record.comments if record else "")
        form.addRow("Respondent / ID", self.respondent); form.addRow("Category", self.category); form.addRow("Rating", self.rating); form.addRow("Response date", self.date); form.addRow("Comments", self.comments)
        buttons = QHBoxLayout(); cancel = QPushButton("Cancel"); cancel.setObjectName("cancel"); save = QPushButton("Save response"); cancel.clicked.connect(self.reject); save.clicked.connect(self.accept); buttons.addWidget(cancel); buttons.addWidget(save); form.addRow(buttons)
    def values(self):
        return (self.respondent.text(), self.category.currentText(), self.rating.value(), self.date.date().toString("yyyy-MM-dd"), self.comments.toPlainText())

class ChartWidget(QWidget):
    def __init__(self, records, chart_type="bar", parent=None):
        super().__init__(parent); lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0)
        fig=Figure(figsize=(6,3.1), dpi=100); self.canvas=FigureCanvasQTAgg(fig); lay.addWidget(self.canvas); ax=fig.add_subplot(111)
        cats=summarize(records)["categories"]
        if not cats: ax.text(.5,.5,"No survey records yet",ha="center",va="center",color="#8290a3"); ax.axis("off")
        elif chart_type=="pie": ax.pie(list(cats.values()), labels=list(cats.keys()), autopct="%1.0f%%", startangle=90); ax.axis("equal")
        elif chart_type=="line":
            trend=summarize(records)["trend"]
            if trend: ax.plot(list(trend.keys()),list(trend.values()),marker="o",linewidth=2,color=TEAL); ax.set_ylabel("Avg rating"); ax.tick_params(axis="x",rotation=30)
            else: ax.bar(list(cats.keys()),list(cats.values()),color=BLUE); ax.tick_params(axis="x",rotation=25)
        else: ax.bar(list(cats.keys()),list(cats.values()),color=BLUE); ax.set_ylabel("Responses"); ax.tick_params(axis="x",rotation=25)
        fig.tight_layout(); self.canvas.draw()

class MainWindow(QMainWindow):
    def __init__(self, records, storage):
        super().__init__(); self.records=records; self.storage=storage; self.threshold=50; self.current_page="Dashboard"
        self.setWindowTitle("Survey Result Explorer"); self.resize(1320,850); self.setMinimumSize(1050,700)
        self.setStyleSheet(f"QMainWindow{{background:{BG};}} QLabel{{color:{TEXT};}} QPushButton{{border:0;border-radius:8px;padding:9px 13px;background:#e8edf5;color:#24354d;font-weight:600;}} QPushButton:hover{{background:#dce5f2;}} QLineEdit,QComboBox,QDateEdit{{background:white;border:1px solid #dbe3ee;border-radius:8px;padding:8px;color:#23354d;}} QTableWidget{{background:white;border:1px solid #e1e8f0;border-radius:10px;gridline-color:#edf1f6;selection-background-color:#dbe8ff;selection-color:#18304b;}} QHeaderView::section{{background:#f4f7fb;color:#5c6b80;border:0;padding:10px;font-weight:600;}}")
        central=QWidget(); self.setCentralWidget(central); outer=QHBoxLayout(central); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        sidebar=QFrame(); sidebar.setFixedWidth(228); sidebar.setStyleSheet(f"background:{NAVY};"); sl=QVBoxLayout(sidebar); sl.setContentsMargins(18,22,16,20); sl.setSpacing(7)
        brand=QLabel("◈  Survey Explorer"); brand.setStyleSheet("color:white;font-size:18px;font-weight:800;padding:6px 0 22px;"); sl.addWidget(brand)
        sl.addWidget(self.nav_label("WORKSPACE"))
        self.stack=QStackedWidget(); self.pages={}
        for name,icon in [("Dashboard","▦"),("Survey Records","▤"),("Add Response","＋"),("Search & Filter","⌕"),("Analytics","▥"),("Reports & Export","⇩")]:
            btn=QPushButton(f"{icon}   {name}"); btn.setCursor(Qt.PointingHandCursor); btn.setStyleSheet("QPushButton{background:transparent;color:#c5d1e2;text-align:left;padding:12px;border-radius:8px;} QPushButton:hover{background:#2b4260;color:white;}"); btn.clicked.connect(lambda _,n=name:self.show_page(n)); sl.addWidget(btn)
        sl.addStretch(); sl.addWidget(self.nav_label("DATA STATUS")); status=QLabel("●  Local storage active\n   CSV + JSON synced"); status.setStyleSheet("color:#82d9c4;font-size:12px;padding:10px;"); sl.addWidget(status)
        outer.addWidget(sidebar); right=QWidget(); rl=QVBoxLayout(right); rl.setContentsMargins(26,20,26,20); rl.setSpacing(16)
        header=QHBoxLayout(); self.heading=QLabel("Dashboard"); self.heading.setStyleSheet("font-size:24px;font-weight:800;color:#18283d;"); header.addWidget(self.heading); header.addStretch(); self.top_add=QPushButton("＋  Add response"); self.top_add.setStyleSheet(f"background:{BLUE};color:white;"); self.top_add.clicked.connect(lambda:self.show_page("Add Response")); header.addWidget(self.top_add); rl.addLayout(header)
        self.stack.setStyleSheet("background:transparent;"); rl.addWidget(self.stack); outer.addWidget(right,1)
        self._build_pages(); self.show_page("Dashboard")
    def nav_label(self,text):
        l=QLabel(text); l.setStyleSheet("color:#7286a0;font-size:10px;font-weight:700;padding:12px 4px 6px;"); return l
    def _build_pages(self):
        self.pages["Dashboard"]=self.dashboard_page(); self.pages["Survey Records"]=self.records_page(); self.pages["Add Response"]=self.add_page(); self.pages["Search & Filter"]=self.search_page(); self.pages["Analytics"]=self.analytics_page(); self.pages["Reports & Export"]=self.reports_page()
        for p in self.pages.values(): self.stack.addWidget(p)
    def show_page(self,name): self.current_page=name; self.heading.setText(name); self.stack.setCurrentWidget(self.pages[name]); self.refresh_all()
    def card(self,title,value,sub="",accent=BLUE):
        f=QFrame(); f.setStyleSheet("QFrame{background:white;border:1px solid #e6ebf2;border-radius:12px;}"); l=QVBoxLayout(f); l.setContentsMargins(17,15,17,15); t=QLabel(title.upper()); t.setStyleSheet(f"color:{MUTED};font-size:10px;font-weight:700;"); v=QLabel(str(value)); v.setStyleSheet(f"color:{TEXT};font-size:27px;font-weight:800;"); s=QLabel(sub); s.setStyleSheet(f"color:{accent};font-size:11px;font-weight:600;"); l.addWidget(t); l.addWidget(v); l.addWidget(s); f.value_label=v; f.sub_label=s; return f
    def dashboard_page(self):
        page=QWidget(); l=QVBoxLayout(page); l.setSpacing(14)
        cards=QHBoxLayout(); self.d_total=self.card("Total responses","0","All collected responses",BLUE); self.d_avg=self.card("Average rating","0","Out of 100",TEAL); self.d_categories=self.card("Categories","0","Survey topic groups",BLUE); self.d_quality=self.card("High ratings","0","Ratings of 80+",TEAL)
        for c in [self.d_total,self.d_avg,self.d_categories,self.d_quality]: cards.addWidget(c)
        l.addLayout(cards)
        middle=QHBoxLayout(); self.d_chart=QFrame(); self.d_chart.setStyleSheet("background:white;border:1px solid #e6ebf2;border-radius:12px;"); self.d_chart_layout=QVBoxLayout(self.d_chart); middle.addWidget(self.d_chart,2)
        insights_box=QFrame(); insights_box.setStyleSheet("background:white;border:1px solid #e6ebf2;border-radius:12px;"); il=QVBoxLayout(insights_box); title=QLabel("Quick insights"); title.setStyleSheet("font-size:15px;font-weight:700;"); il.addWidget(title); self.insights_list=QListWidget(); self.insights_list.setStyleSheet("border:0;background:transparent;color:#35465d;"); il.addWidget(self.insights_list); middle.addWidget(insights_box,1); l.addLayout(middle)
        quick=QHBoxLayout(); for_btn=[("Add new response","Add Response"),("View records","Survey Records"),("Explore analytics","Analytics")]
        for label,nav in for_btn:
            b=QPushButton(label); b.clicked.connect(lambda _,n=nav:self.show_page(n)); quick.addWidget(b)
        l.addLayout(quick); l.addStretch(); return page
    def records_page(self):
        page=QWidget(); l=QVBoxLayout(page); top=QHBoxLayout(); label=QLabel("Manage all survey responses"); label.setStyleSheet("color:#66768b;"); top.addWidget(label); top.addStretch(); b=QPushButton("＋ Add record"); b.clicked.connect(lambda:self.show_page("Add Response")); top.addWidget(b); l.addLayout(top)
        self.records_table=self.make_table(); l.addWidget(self.records_table)
        actions=QHBoxLayout(); edit=QPushButton("Edit selected"); delete=QPushButton("Delete selected"); clean=QPushButton("Clean dataset"); edit.clicked.connect(self.edit_selected); delete.clicked.connect(self.delete_selected); clean.clicked.connect(self.clean_dataset); actions.addWidget(edit); actions.addWidget(delete); actions.addStretch(); actions.addWidget(clean); l.addLayout(actions); return page
    def make_table(self):
        t=QTableWidget(0,6); t.setHorizontalHeaderLabels(["Respondent","Category","Rating","Date","Comments","ID"]); t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); t.setSelectionBehavior(QAbstractItemView.SelectRows); t.setSelectionMode(QAbstractItemView.SingleSelection); t.setEditTriggers(QAbstractItemView.NoEditTriggers); t.verticalHeader().setVisible(False); t.setAlternatingRowColors(True); t.setStyleSheet(t.styleSheet()+"QTableWidget{alternate-background-color:#f8fafc;}"); return t
    def add_page(self):
        page=QWidget(); l=QVBoxLayout(page); f=QFrame(); f.setStyleSheet("background:white;border:1px solid #e6ebf2;border-radius:12px;"); fl=QVBoxLayout(f); fl.setContentsMargins(22,22,22,22); h=QLabel("Capture a survey response"); h.setStyleSheet("font-size:18px;font-weight:800;"); fl.addWidget(h); note=QLabel("All entries are validated before saving."); note.setStyleSheet(f"color:{MUTED};"); fl.addWidget(note)
        form=QFormLayout(); self.add_name=QLineEdit(); self.add_name.setPlaceholderText("Respondent or anonymous ID"); self.add_category=QComboBox(); self.add_category.setEditable(True); self.add_category.addItems(["Academics","Campus Facilities","Student Services","Technology","Events","Food","Other"]); self.add_rating=QDoubleSpinBox(); self.add_rating.setRange(0,100); self.add_rating.setDecimals(1); self.add_rating.setSuffix(" / 100"); self.add_rating.setValue(75); self.add_date=QDateEdit(); self.add_date.setCalendarPopup(True); self.add_date.setDate(date.today()); self.add_date.setDisplayFormat("yyyy-MM-dd"); self.add_comments=QTextEdit(); self.add_comments.setMaximumHeight(100)
        form.addRow("Respondent / ID *",self.add_name); form.addRow("Category *",self.add_category); form.addRow("Rating *",self.add_rating); form.addRow("Date *",self.add_date); form.addRow("Comments",self.add_comments); fl.addLayout(form)
        row=QHBoxLayout(); save=QPushButton("Save response"); save.setStyleSheet(f"background:{BLUE};color:white;"); clear=QPushButton("Clear form"); save.clicked.connect(self.save_new); clear.clicked.connect(self.clear_form); row.addWidget(save); row.addWidget(clear); row.addStretch(); fl.addLayout(row); l.addWidget(f); l.addStretch(); return page
    def search_page(self):
        page=QWidget(); l=QVBoxLayout(page); box=QFrame(); box.setStyleSheet("background:white;border:1px solid #e6ebf2;border-radius:12px;"); bl=QVBoxLayout(box); row=QHBoxLayout(); self.search_input=QLineEdit(); self.search_input.setPlaceholderText("Search respondent, category, comments..."); self.search_category=QComboBox(); self.search_category.addItem("All"); self.search_from=QDateEdit(); self.search_from.setCalendarPopup(True); self.search_from.setDisplayFormat("yyyy-MM-dd"); self.search_from.setSpecialValueText("Start date"); self.search_from.setDate(self.search_from.minimumDate()); self.search_to=QDateEdit(); self.search_to.setCalendarPopup(True); self.search_to.setDisplayFormat("yyyy-MM-dd"); self.search_to.setSpecialValueText("End date"); self.search_to.setDate(self.search_to.minimumDate()); go=QPushButton("Search"); reset=QPushButton("Reset"); go.clicked.connect(self.run_search); reset.clicked.connect(self.reset_search); row.addWidget(self.search_input,2); row.addWidget(self.search_category); row.addWidget(self.search_from); row.addWidget(self.search_to); row.addWidget(go); row.addWidget(reset); bl.addLayout(row); l.addWidget(box)
        self.search_table=self.make_table(); l.addWidget(self.search_table); self.search_count=QLabel("Enter search criteria or browse all responses."); self.search_count.setStyleSheet(f"color:{MUTED};"); l.addWidget(self.search_count); l.addStretch(); return page
    def analytics_page(self):
        page=QWidget(); l=QVBoxLayout(page); controls=QHBoxLayout(); self.chart_select=QComboBox(); self.chart_select.addItems(["Category counts (Bar)","Category share (Pie)","Average rating trend (Line)"]); refresh=QPushButton("Refresh chart"); refresh.clicked.connect(self.refresh_analytics_chart); controls.addWidget(QLabel("Chart type")); controls.addWidget(self.chart_select); controls.addWidget(refresh); controls.addStretch(); l.addLayout(controls)
        self.analytics_summary=QLabel(); self.analytics_summary.setStyleSheet("font-size:14px;font-weight:700;color:#30435d;background:white;padding:12px;border-radius:8px;"); l.addWidget(self.analytics_summary); self.analytics_chart_frame=QFrame(); self.analytics_chart_frame.setStyleSheet("background:white;border:1px solid #e6ebf2;border-radius:12px;"); self.analytics_chart_layout=QVBoxLayout(self.analytics_chart_frame); l.addWidget(self.analytics_chart_frame,1)
        threshold_row=QHBoxLayout(); threshold_row.addWidget(QLabel("Low-rating warning threshold:")); self.threshold_spin=QDoubleSpinBox(); self.threshold_spin.setRange(0,100); self.threshold_spin.setValue(self.threshold); self.threshold_spin.setSuffix(" / 100"); self.threshold_spin.valueChanged.connect(lambda v:setattr(self,"threshold",v)); threshold_row.addWidget(self.threshold_spin); threshold_row.addWidget(QLabel("Responses below this score will be flagged.")); threshold_row.addStretch(); l.addLayout(threshold_row); self.warning=QLabel(); self.warning.setStyleSheet("color:#b66b17;font-weight:600;"); l.addWidget(self.warning); return page
    def reports_page(self):
        page=QWidget(); l=QVBoxLayout(page); f=QFrame(); f.setStyleSheet("background:white;border:1px solid #e6ebf2;border-radius:12px;"); fl=QVBoxLayout(f); title=QLabel("Export & reports"); title.setStyleSheet("font-size:18px;font-weight:800;"); fl.addWidget(title); desc=QLabel("Export your data and findings for presentation, sharing, or further analysis."); desc.setStyleSheet(f"color:{MUTED};"); fl.addWidget(desc)
        for label,fn in [("Export records as CSV",lambda:self.export_data("csv")),("Export records as JSON",lambda:self.export_data("json")),("Generate executive summary (Markdown)",lambda:self.export_summary_file("md")),("Generate plain-text report",lambda:self.export_summary_file("txt")),("Save category chart as PNG",self.save_chart), ("Import survey CSV",self.import_csv)]:
            b=QPushButton(label); b.setStyleSheet("text-align:left;padding:13px;background:#f2f6fb;"); b.clicked.connect(fn); fl.addWidget(b)
        l.addWidget(f); audit=QLabel("Audit log and backup files are stored locally in the data folder."); audit.setStyleSheet(f"color:{MUTED};padding:8px;"); l.addWidget(audit); l.addStretch(); return page
    def refresh_all(self):
        if not self.pages: return
        s=summarize(self.records); self.d_total.value_label.setText(str(s["total"]))
        self.d_avg.value_label.setText(f"{s['average']:.1f}"); self.d_categories.value_label.setText(str(len(s["categories"])))
        self.d_quality.value_label.setText(str(s["high"]))
        self.insights_list.clear(); self.insights_list.addItems(insights(self.records))
        for frame,layout in [(self.d_chart,self.d_chart_layout)]:
            while layout.count(): item=layout.takeAt(0); w=item.widget(); w.deleteLater() if w else None
            layout.addWidget(QLabel("Response distribution")); layout.addWidget(ChartWidget(self.records,"bar"))
        self.fill_table(self.records_table,self.records)
        self.search_category.clear(); self.search_category.addItem("All"); self.search_category.addItems(sorted(s["categories"].keys()))
        if self.current_page=="Search & Filter": self.run_search()
        if self.current_page=="Analytics": self.refresh_analytics_chart()
    def fill_table(self,table,records):
        table.setRowCount(len(records))
        for i,r in enumerate(records):
            for j,val in enumerate([r.respondent,r.category,f"{float(r.rating):.1f}",r.response_date,r.comments,r.id]):
                it=QTableWidgetItem(str(val)); it.setToolTip(str(val)); table.setItem(i,j,it)
    def save_new(self):
        try:
            values=validate_record(self.add_name.text(),self.add_category.currentText(),self.add_rating.value(),self.add_date.date().toString("yyyy-MM-dd"),self.add_comments.toPlainText())
            r=SurveyRecord.create(*values[:4],comments=values[4]); self.records.append(r); self.persist("Added",r.id); QMessageBox.information(self,"Saved","Survey response saved successfully."); self.clear_form(); self.show_page("Survey Records")
        except ValidationError as e: QMessageBox.warning(self,"Validation error",str(e))
    def clear_form(self): self.add_name.clear(); self.add_category.setCurrentIndex(0); self.add_rating.setValue(75); self.add_date.setDate(date.today()); self.add_comments.clear()
    def selected_record(self,table):
        rows=table.selectionModel().selectedRows(); return self.records[rows[0].row()] if rows else None
    def edit_selected(self):
        r=self.selected_record(self.records_table)
        if not r: QMessageBox.information(self,"Select record","Please select a row first."); return
        dlg=RecordDialog(self,r)
        if dlg.exec():
            try:
                vals=validate_record(*dlg.values()); r.respondent,r.category,r.rating,r.response_date,r.comments=vals; self.persist("Edited",r.id); self.refresh_all()
            except ValidationError as e: QMessageBox.warning(self,"Validation error",str(e))
    def delete_selected(self):
        r=self.selected_record(self.records_table)
        if not r: QMessageBox.information(self,"Select record","Please select a row first."); return
        if QMessageBox.question(self,"Delete response",f"Delete response for {r.respondent}?") == QMessageBox.Yes:
            self.records.remove(r); self.persist("Deleted",r.id); self.refresh_all()
    def clean_dataset(self):
        cleaned,report=clean_records(self.records); text=f"Original: {report['original']}\nAfter cleaning: {report['cleaned']}\nDuplicates removed: {report['duplicates_removed']}\nInvalid rows: {len(report['invalid'])}"
        if report["invalid"]: text += "\n\nInvalid rows:\n"+"\n".join(f"Row {e['row']}: {e['error']}" for e in report["invalid"][:10])
        QMessageBox.information(self,"Cleaning results",text)
        if cleaned!=self.records: self.records=cleaned; self.persist("Cleaned dataset",text); self.refresh_all()
    def run_search(self):
        if not hasattr(self,"search_table"): return
        cat=self.search_category.currentText() if self.search_category.count() else "All"; start=self.search_from.date().toString("yyyy-MM-dd") if self.search_from.date()!=self.search_from.minimumDate() else ""; end=self.search_to.date().toString("yyyy-MM-dd") if self.search_to.date()!=self.search_to.minimumDate() else ""
        result=filter_records(self.records,self.search_input.text(),cat,start,end); self.fill_table(self.search_table,result); self.search_count.setText(f"{len(result)} response(s) found")
    def reset_search(self): self.search_input.clear(); self.search_category.setCurrentIndex(0); self.search_from.setDate(self.search_from.minimumDate()); self.search_to.setDate(self.search_to.minimumDate()); self.run_search()
    def refresh_analytics_chart(self):
        if not hasattr(self,"analytics_chart_layout"): return
        s=summarize(self.records); self.analytics_summary.setText(f"{s['total']} responses   ·   Average rating {s['average']:.1f}/100   ·   {len(s['categories'])} categories")
        mode=self.chart_select.currentIndex(); chart=ChartWidget(self.records,["bar","pie","line"][mode]); layout=self.analytics_chart_layout
        while layout.count(): item=layout.takeAt(0); w=item.widget(); w.deleteLater() if w else None
        layout.addWidget(chart); lows=[r for r in self.records if float(r.rating)<self.threshold]; self.warning.setText(f"⚠ {len(lows)} response(s) below threshold {self.threshold:.0f}." if lows else "✓ No responses below the warning threshold.")
    def persist(self,action,details): self.storage.save(self.records); self.storage.log(action,details); self.refresh_all()
    def export_data(self,fmt):
        path,_=QFileDialog.getSaveFileName(self,"Export records",f"survey_records.{fmt}",f"{fmt.upper()} files (*.{fmt})")
        if path:
            try: export_records(self.records,path,fmt); QMessageBox.information(self,"Export complete",f"Saved {len(self.records)} records to:\n{path}")
            except Exception as e: QMessageBox.critical(self,"Export failed",str(e))
    def export_summary_file(self,fmt):
        ext="md" if fmt=="md" else "txt"; path,_=QFileDialog.getSaveFileName(self,"Save summary",f"survey_summary.{ext}",f"Files (*.{ext})")
        if path:
            try: export_summary(self.records,path,fmt); QMessageBox.information(self,"Report ready",f"Summary saved:\n{path}")
            except Exception as e: QMessageBox.critical(self,"Report failed",str(e))
    def save_chart(self):
        path,_=QFileDialog.getSaveFileName(self,"Save chart","survey_chart.png","PNG image (*.png)")
        if path:
            fig=Figure(figsize=(8,4)); ax=fig.add_subplot(111); cats=summarize(self.records)["categories"]
            if cats: ax.bar(list(cats.keys()),list(cats.values()),color=BLUE); ax.set_ylabel("Responses"); ax.tick_params(axis="x",rotation=25)
            fig.tight_layout(); fig.savefig(path,dpi=160); QMessageBox.information(self,"Chart saved",path)
    def import_csv(self):
        path,_=QFileDialog.getOpenFileName(self,"Import survey CSV","","CSV files (*.csv)")
        if not path: return
        imported=[]; errors=[]
        with open(path,newline="",encoding="utf-8-sig") as f:
            reader=csv.DictReader(f); fields={x.lower().strip() for x in (reader.fieldnames or [])}
            if not {"respondent","category","rating","response_date"}.issubset(fields): QMessageBox.warning(self,"CSV format","Required columns: respondent, category, rating, response_date. Optional: id, comments."); return
            for idx,row in enumerate(reader,2):
                row={k.lower().strip():v for k,v in row.items() if k}
                try:
                    values=validate_record(row.get("respondent"),row.get("category"),row.get("rating"),row.get("response_date"),row.get("comments","")); imported.append(SurveyRecord.create(*values[:4],comments=values[4]))
                except ValidationError as e: errors.append(f"Row {idx}: {e}")
        if imported:
            self.records.extend(imported); self.persist("Imported CSV",f"{len(imported)} records from {Path(path).name}")
        message=f"Imported {len(imported)} valid row(s).\nRejected {len(errors)} row(s)."
        if errors: message+="\n\n"+"\n".join(errors[:12])
        QMessageBox.information(self,"Import results",message)
