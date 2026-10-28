import os
import sys
import json
from flask import Flask, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename

# Ensure UTF-8
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from data_engine import load_all_data, DATA_EXCEL_PATH, CACHE_JSON_PATH
from analytics_engine import AnalyticsEngine
from export_engine import ExportEngine
from import_engine import parse_raw_sql_file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__, static_folder=STATIC_DIR)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 50 MB max

analytics = AnalyticsEngine()
exporter = ExportEngine(analytics)

@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory(STATIC_DIR, path)

@app.route('/api/metadata', methods=['GET'])
def get_metadata():
    try:
        d = analytics.data
        return jsonify({
            'success': True,
            'available_months': d.get('available_months', []),
            'units': d.get('units', []),
            'banks': d.get('banks', []),
            'categories': d.get('categories', [])
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/overview', methods=['GET'])
def get_overview():
    try:
        month = request.args.get('month', 'Thang 09')
        unit = request.args.get('unit', 'TOÀN CÔNG TY')
        ov = analytics.get_overview(month, unit)
        return jsonify({'success': True, 'data': ov})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rankings', methods=['GET'])
def get_rankings():
    try:
        month = request.args.get('month', 'Thang 09')
        ranks = analytics.get_unit_rankings(month)
        return jsonify({'success': True, 'data': ranks})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/banks', methods=['GET'])
def get_banks():
    try:
        month = request.args.get('month', 'Thang 09')
        unit = request.args.get('unit', 'TOÀN CÔNG TY')
        info = analytics.get_bank_breakdown(month, unit)
        return jsonify({'success': True, 'data': info})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trends', methods=['GET'])
def get_trends():
    try:
        unit = request.args.get('unit', 'TOÀN CÔNG TY')
        trends = analytics.get_time_series(unit)
        return jsonify({'success': True, 'data': trends})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analysis', methods=['GET'])
def get_analysis():
    try:
        month = request.args.get('month', 'Thang 09')
        rep = analytics.generate_expert_report(month)
        return jsonify({'success': True, 'data': rep})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reload', methods=['POST', 'GET'])
def reload_data():
    global analytics, exporter
    try:
        new_data = load_all_data(force_reload=True)
        analytics = AnalyticsEngine(new_data)
        exporter = ExportEngine(analytics)
        return jsonify({
            'success': True, 
            'message': 'Đã làm mới dữ liệu thành công từ file Ngan hang 2026.xlsm!',
            'available_months': new_data.get('available_months', [])
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    global analytics, exporter
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Chưa chọn file tải lên'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Tên file không hợp lệ'}), 400
            
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_DIR, filename)
        file.save(save_path)
        
        month_label = request.form.get('month_label', '').strip()
        is_sql = request.form.get('is_sql', 'false').lower() == 'true'
        
        if is_sql or 'thang' in filename.lower() and not filename.lower().endswith('.xlsm'):
            if not month_label:
                # auto extract month from filename e.g. Thang 102026.xlsx -> Thang 10
                import re
                m_match = re.search(r'(\d{1,2})', filename)
                if m_match:
                    month_label = f"Thang {int(m_match.group(1)):02d}"
                else:
                    month_label = "Tháng Mới"
                    
            res = parse_raw_sql_file(save_path, month_label)
            analytics = AnalyticsEngine(res)
            exporter = ExportEngine(analytics)
            return jsonify({
                'success': True,
                'message': f'Đã nạp thành công dữ liệu SQL cho kỳ {month_label}!',
                'month': month_label
            })
        else:
            # Overwrite or parse as master excel
            new_data = load_all_data(excel_path=save_path, force_reload=True)
            analytics = AnalyticsEngine(new_data)
            exporter = ExportEngine(analytics)
            return jsonify({
                'success': True,
                'message': f'Đã nạp và cập nhật toàn bộ cơ sở dữ liệu từ file {filename}!',
                'available_months': new_data.get('available_months', [])
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export/docx', methods=['GET'])
def export_docx():
    try:
        month = request.args.get('month', 'Thang 09')
        out_name = f"Bao_Cao_Thu_Ngan_Hang_{month.replace(' ', '_')}.docx"
        out_path = os.path.join(BASE_DIR, out_name)
        exporter.generate_docx_report(month, out_path)
        return send_file(out_path, as_attachment=True, download_name=out_name)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export/excel', methods=['GET'])
def export_excel():
    try:
        month = request.args.get('month', 'Thang 09')
        out_name = f"Tong_Hop_Bao_Cao_{month.replace(' ', '_')}.xlsx"
        out_path = os.path.join(BASE_DIR, out_name)
        exporter.generate_excel_report(month, out_path)
        return send_file(out_path, as_attachment=True, download_name=out_name)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5678))
    print(f"EVN LAM DONG - BANK REPORT SERVER IS RUNNING ON http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
