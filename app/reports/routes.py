from flask import request, render_template, url_for, redirect
from app.reports import reports_bp
from reporting import ReportFactory
from reporting.detailed_report import DetailedReport
from app.models import Promotion


@reports_bp.route("/", methods=["POST", "GET"])
def reports_index():
    next_page = {
        "promotion": "reports_bp.promotion_reports",
        "detailed": "reports_bp.detailed_reports",
    }
    if request.method == "POST":
        return redirect(url_for(next_page.get(request.form.get("report-type"))))
    return render_template("reports/choose-report.html")


@reports_bp.route("/promotions", methods=["POST", "GET"])
def promotion_reports():

    if request.method == "POST":
        form_data = request.form.to_dict()
        report = ReportFactory.create_report(
            report_type=form_data.pop("report-type"), **form_data
        )
        return report.return_data()
    return render_template(
        "reports/promotion-report.html", page_header="Promotion report"
    )


@reports_bp.route("/detailed", methods=["POST", "GET"])
def detailed_reports():
    if request.method == "POST":
        form_data = request.form.to_dict()
        report = DetailedReport(
            form_data.get("year"),
            form_data.get("scheme"),
            form_data.get("promotion-type"),
        )
        return report.return_data()
    return render_template(
        "reports/detailed-report.html",
        page_header="Detailed Report",
        promotion_types=Promotion.query.all(),
    )
