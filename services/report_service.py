"""Report generation service."""
from pathlib import Path
import config
class ReportService:
    def __init__(self,repository=None):
        self.repository=repository; Path(config.REPORTS_PATH).mkdir(parents=True,exist_ok=True)
    def generate_daily_report(self,rows,output_path=None):
        output=Path(output_path or Path(config.REPORTS_PATH)/"batteryems_daily_report.pdf")
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table
        from reportlab.lib.styles import getSampleStyleSheet
        styles=getSampleStyleSheet(); doc=SimpleDocTemplate(str(output),pagesize=A4)
        story=[Paragraph("BatteryEMS Daily Report",styles["Title"]),Spacer(1,12),Paragraph(f"Readings: {len(rows)}",styles["Normal"])]
        if rows:
            r=rows[-1]
            story.append(Table([["Timestamp","SOC %","SOH %","Pack V","Current A","Temp °C","Status","Grid"],
                                [r.get("timestamp",""),r.get("soc_percent",""),r.get("soh_percent",""),r.get("pack_voltage",""),r.get("pack_current",""),r.get("temperature",""),r.get("battery_status",""),r.get("grid_status","")]]))
        doc.build(story); return str(output)
