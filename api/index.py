from datetime import datetime
from flask import Flask, render_template_string, request
import pandas as pd

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>مراقب انتهاء الشهادات والتصاريح</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 900px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        h2 { color: #1e3a8a; text-align: center; margin-bottom: 25px; }
        .upload-box { border: 2px dashed #93c5fd; padding: 25px; text-align: center; border-radius: 10px; background: #eff6ff; margin-bottom: 25px; }
        input[type="file"] { margin: 15px 0; padding: 10px; background: white; border-radius: 6px; border: 1px solid #cbd5e1; }
        button { background-color: #2563eb; color: white; border: none; padding: 12px 30px; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; transition: background 0.2s; }
        button:hover { background-color: #1d4ed8; }
        table { width: 100%; border-collapse: collapse; margin-top: 25px; }
        th, td { padding: 14px 16px; text-align: right; border-bottom: 1px solid #e2e8f0; }
        th { background-color: #f1f5f9; color: #334155; font-weight: 600; }
        .alert-row { background-color: #fef2f2; color: #991b1b; font-weight: bold; }
        .safe-row { background-color: #f0fdf4; color: #166534; }
        .badge { display: inline-block; padding: 5px 12px; border-radius: 20px; font-size: 13px; }
        .badge-danger { background-color: #fee2e2; color: #dc2626; border: 1px solid #fecaca; }
        .badge-safe { background-color: #dcfce7; color: #16a34a; border: 1px solid #bbf7d0; }
        .msg { padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; background: #e0f2fe; color: #0369a1; font-weight: 500; }
        .instructions { background: #f8fafc; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-right: 4px solid #3b82f6; font-size: 14px; color: #475569; }
    </style>
</head>
<body>
    <div class="container">
        <h2>📊 نظام متابعة صلاحية الشهادات والتصاريح</h2>
        
        <div class="instructions">
            <strong>تعليمات الإستخدام:</strong> قم برفع ملف الإكسيل الذي يحتوي على الأعمدة التالية بالترتيب: 
            <code>العميل</code> ، <code>الشهادة</code> ، <code>تاريخ الانتهاء</code>. وسيقوم النظام فوراً بتنبيهك بالشهادات التي اقتربت من الانتهاء خلال 15 يوماً.
        </div>

        <div class="upload-box">
            <form action="/check" method="post" enctype="multipart/form-data">
                <p>اختر ملف الإكسيل الخاص بالشهادات:</p>
                <input type="file" name="file" accept=".xlsx, .xls" required><br>
                <button type="submit">فحص وعرض النتائج</button>
            </form>
        </div>

        {% if msg %}
        <div class="msg">{{ msg }}</div>
        {% endif %}

        {% if results %}
        <h3>📋 نتائج الفحص والمتابعة:</h3>
        <table>
            <thead>
                <tr>
                    <th>اسم العميل</th>
                    <th>الشهادة / التصريح</th>
                    <th>تاريخ الانتهاء</th>
                    <th>المتبقي (أيام)</th>
                    <th>الحالة</th>
                </tr>
            </thead>
            <tbody>
                {% for row in results %}
                <tr class="{{ 'alert-row' if row.is_alert else 'safe-row' }}">
                    <td>{{ row.client }}</td>
                    <td>{{ row.cert }}</td>
                    <td>{{ row.expiry }}</td>
                    <td>{{ row.days_left }} يوماً</td>
                    <td>
                        {% if row.is_alert %}
                            <span class="badge badge-danger">⚠️ تنبيه (تنتهي قريباً)</span>
                        {% else %}
                            <span class="badge badge-safe">✔ سارية</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/check", methods=["POST"])
def check():
    if 'file' not in request.files:
        return render_template_string(HTML_TEMPLATE, msg="لم يتم اختيار ملف.")
    file = request.files['file']
    try:
        df = pd.read_excel(file)
        required_columns = ["العميل", "الشهادة", "تاريخ الانتهاء"]
        for col in required_columns:
            if col not in df.columns:
                return render_template_string(HTML_TEMPLATE, msg=f"خطأ: العمود الأساسي '{col}' غير موجود في ملف الإكسيل المرفوع.")
        
        today = datetime.now().date()
        results = []
        for _, row in df.iterrows():
            client_name = row["العميل"]
            cert_name = row["الشهادة"]
            expiry_date_raw = row["تاريخ الانتهاء"]
            expiry_date = pd.to_datetime(expiry_date_raw).date()
            delta_days = (expiry_date - today).days
            is_alert = delta_days <= 15
            results.append({
                "client": client_name,
                "cert": cert_name,
                "expiry": str(expiry_date),
                "days_left": delta_days,
                "is_alert": is_alert
            })
        return render_template_string(HTML_TEMPLATE, results=results, msg="تم فحص الملف بنجاح وإظهار حالة جميع الشهادات أدناه.")
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, msg=f"حدث خطأ أثناء معالجة الملف: {str(e)}")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
