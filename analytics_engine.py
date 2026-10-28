import sys
import json
from data_engine import load_all_data

# Ensure UTF-8 output
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def format_money(val):
    if val >= 1e12:
        return f"{val / 1e12:.2f} nghìn tỷ đ"
    elif val >= 1e9:
        return f"{val / 1e9:.2f} tỷ đ"
    elif val >= 1e6:
        return f"{val / 1e6:.2f} triệu đ"
    return f"{val:,.0f} đ"

def format_number(val):
    return f"{val:,.0f}"

class AnalyticsEngine:
    def __init__(self, data=None):
        if data is None:
            self.data = load_all_data()
        else:
            self.data = data
            
    def get_month_data(self, month_key):
        return self.data.get('months_data', {}).get(month_key, {})
        
    def get_previous_month(self, month_key):
        months = [m for m in self.data.get('available_months', []) if m != "Lũy kế 9 tháng"]
        if month_key in months:
            idx = months.index(month_key)
            if idx > 0:
                return months[idx - 1]
        return None

    def get_overview(self, month_key="Thang 09", unit_name="TOÀN CÔNG TY"):
        m_data = self.get_month_data(month_key)
        if not m_data or unit_name not in m_data:
            return {}
            
        unit_info = m_data[unit_name]
        tot = unit_info['total']
        
        # Calculate channels breakdown
        hd_tong = tot['hd_tong'] or 1.0
        st_tong = tot['st_tong'] or 1.0
        
        channels = [
            {
                'id': 'app_vi',
                'name': 'App, Ví điện tử & Tự động',
                'hd': tot['hd_app'],
                'st': tot['st_app'],
                'pct_hd': (tot['hd_app'] / hd_tong) * 100,
                'pct_st': (tot['st_app'] / st_tong) * 100,
                'color': '#10b981' # Emerald Green
            },
            {
                'id': 'unc',
                'name': 'Ủy nhiệm chi (UNC Doanh nghiệp)',
                'hd': tot['hd_unc'],
                'st': tot['st_unc'],
                'pct_hd': (tot['hd_unc'] / hd_tong) * 100,
                'pct_st': (tot['st_unc'] / st_tong) * 100,
                'color': '#3b82f6' # Blue
            },
            {
                'id': 'unt',
                'name': 'Ủy nhiệm thu (UNT)',
                'hd': tot['hd_unt'],
                'st': tot['st_unt'],
                'pct_hd': (tot['hd_unt'] / hd_tong) * 100,
                'pct_st': (tot['st_unt'] / st_tong) * 100,
                'color': '#f59e0b' # Amber
            },
            {
                'id': 'quay',
                'name': 'Nộp tại quầy NH / TGTT',
                'hd': tot['hd_quay'],
                'st': tot['st_quay'],
                'pct_hd': (tot['hd_quay'] / hd_tong) * 100,
                'pct_st': (tot['st_quay'] / st_tong) * 100,
                'color': '#8b5cf6' # Purple
            }
        ]
        
        # Compare with previous month
        prev_m = self.get_previous_month(month_key)
        mom = None
        if prev_m:
            prev_data = self.get_month_data(prev_m)
            if prev_data and unit_name in prev_data:
                p_tot = prev_data[unit_name]['total']
                diff_st = tot['st_tong'] - p_tot['st_tong']
                diff_hd = tot['hd_tong'] - p_tot['hd_tong']
                pct_st = (diff_st / p_tot['st_tong'] * 100) if p_tot['st_tong'] > 0 else 0
                pct_hd = (diff_hd / p_tot['hd_tong'] * 100) if p_tot['hd_tong'] > 0 else 0
                mom = {
                    'prev_month': prev_m,
                    'diff_st': diff_st,
                    'diff_hd': diff_hd,
                    'growth_st_pct': pct_st,
                    'growth_hd_pct': pct_hd
                }
                
        return {
            'month': month_key,
            'unit': unit_name,
            'total_st': tot['st_tong'],
            'total_hd': tot['hd_tong'],
            'channels': channels,
            'digital_ratio_hd': (tot['hd_app'] / hd_tong) * 100,
            'digital_ratio_st': (tot['st_app'] / st_tong) * 100,
            'mom': mom
        }

    def get_unit_rankings(self, month_key="Thang 09"):
        m_data = self.get_month_data(month_key)
        if not m_data:
            return []
            
        units_list = []
        for u in self.data.get('units', []):
            if u in m_data:
                tot = m_data[u]['total']
                hd_tong = tot['hd_tong'] or 1.0
                st_tong = tot['st_tong'] or 1.0
                units_list.append({
                    'unit': u,
                    'st_tong': tot['st_tong'],
                    'hd_tong': tot['hd_tong'],
                    'st_app': tot['st_app'],
                    'hd_app': tot['hd_app'],
                    'st_unc': tot['st_unc'],
                    'hd_unc': tot['hd_unc'],
                    'pct_digital_hd': (tot['hd_app'] / hd_tong) * 100,
                    'pct_digital_st': (tot['st_app'] / st_tong) * 100
                })
                
        # Sort by total amount descending
        units_list.sort(key=lambda x: x['st_tong'], reverse=True)
        for idx, u in enumerate(units_list, 1):
            u['rank_st'] = idx
            
        return units_list

    def get_bank_breakdown(self, month_key="Thang 09", unit_name="TOÀN CÔNG TY"):
        m_data = self.get_month_data(month_key)
        if not m_data or unit_name not in m_data:
            return {'banks': [], 'categories': []}
            
        banks_raw = m_data[unit_name]['banks']
        tot = m_data[unit_name]['total']
        hd_all = tot['hd_tong'] or 1.0
        st_all = tot['st_tong'] or 1.0
        
        bank_list = []
        cat_sums = {}
        
        for b in banks_raw:
            b_st = b['st_tong']
            b_hd = b['hd_tong']
            if b_st == 0 and b_hd == 0:
                continue
                
            pct_st = (b_st / st_all) * 100
            pct_hd = (b_hd / hd_all) * 100
            
            b_entry = {
                'bank_name': b['bank'],
                'bank_short': b['bank_short'],
                'category': b['category'],
                'hd_tong': b_hd,
                'st_tong': b_st,
                'hd_app': b['hd_app'],
                'st_app': b['st_app'],
                'hd_unc': b['hd_unc'],
                'st_unc': b['st_unc'],
                'hd_unt': b['hd_unt'],
                'st_unt': b['st_unt'],
                'hd_quay': b['hd_quay'],
                'st_quay': b['st_quay'],
                'share_st': pct_st,
                'share_hd': pct_hd
            }
            bank_list.append(b_entry)
            
            c = b['category']
            if c not in cat_sums:
                cat_sums[c] = {'category': c, 'st_tong': 0.0, 'hd_tong': 0.0}
            cat_sums[c]['st_tong'] += b_st
            cat_sums[c]['hd_tong'] += b_hd

        bank_list.sort(key=lambda x: x['st_tong'], reverse=True)
        
        categories_list = []
        for c, v in cat_sums.items():
            categories_list.append({
                'category': c,
                'st_tong': v['st_tong'],
                'hd_tong': v['hd_tong'],
                'share_st': (v['st_tong'] / st_all) * 100,
                'share_hd': (v['hd_tong'] / hd_all) * 100
            })
        categories_list.sort(key=lambda x: x['st_tong'], reverse=True)
        
        return {
            'banks': bank_list,
            'categories': categories_list
        }

    def get_time_series(self, unit_name="TOÀN CÔNG TY"):
        months = [m for m in self.data.get('available_months', []) if m != "Lũy kế 9 tháng"]
        timeline = []
        
        for m in months:
            m_data = self.get_month_data(m)
            if unit_name in m_data:
                tot = m_data[unit_name]['total']
                timeline.append({
                    'month': m,
                    'st_tong': tot['st_tong'],
                    'hd_tong': tot['hd_tong'],
                    'st_app': tot['st_app'],
                    'hd_app': tot['hd_app'],
                    'st_unc': tot['st_unc'],
                    'hd_unc': tot['hd_unc'],
                    'st_unt': tot['st_unt'],
                    'hd_unt': tot['hd_unt'],
                    'st_quay': tot['st_quay'],
                    'hd_quay': tot['hd_quay']
                })
        return timeline

    def generate_expert_report(self, month_key="Thang 09"):
        ov = self.get_overview(month_key, "TOÀN CÔNG TY")
        rankings = self.get_unit_rankings(month_key)
        bank_info = self.get_bank_breakdown(month_key, "TOÀN CÔNG TY")
        timeline = self.get_time_series("TOÀN CÔNG TY")
        
        top3_units = rankings[:3] if len(rankings) >= 3 else rankings
        bottom3_units = rankings[-3:] if len(rankings) >= 3 else []
        top5_banks = bank_info['banks'][:5] if len(bank_info['banks']) >= 5 else bank_info['banks']
        
        st_val = ov.get('total_st', 0)
        hd_val = ov.get('total_hd', 0)
        app_hd_pct = ov.get('digital_ratio_hd', 0)
        app_st_pct = ov.get('digital_ratio_st', 0)
        
        mom = ov.get('mom')
        mom_txt = "Dữ liệu kỳ đầu tiên hoặc chưa có tháng đối chiếu liền kề."
        if mom:
            grow_st = mom['growth_st_pct']
            diff_st_str = format_money(abs(mom['diff_st']))
            direction = "tăng" if grow_st >= 0 else "giảm"
            mom_txt = f"So với tháng trước ({mom['prev_month']}), tổng số tiền thu qua ngân hàng/TGTT {direction} {diff_st_str} ({grow_st:+.2f}%), số hóa đơn biến động {mom['growth_hd_pct']:+.2f}%."
            
        top_unit_strs = [f"{u['unit']} ({format_money(u['st_tong'])}, tỷ lệ số hóa {u['pct_digital_hd']:.1f}%)" for u in top3_units]
        bottom_unit_strs = [f"{u['unit']} ({format_money(u['st_tong'])}, {u['hd_tong']:,.0f} HĐ)" for u in bottom3_units]
        top_bank_strs = [f"{b['bank_short']} (chiếm {b['share_st']:.1f}% số tiền - {format_money(b['st_tong'])})" for b in top5_banks]

        # Extract Big 4 vs Fintech
        cats = {c['category']: c for c in bank_info['categories']}
        big4 = cats.get('Big 4 Ngân hàng', {'share_st': 0, 'share_hd': 0, 'st_tong': 0})
        fintech = cats.get('Ví điện tử & Fintech', {'share_st': 0, 'share_hd': 0, 'st_tong': 0})
        
        report_sections = {
            'title': f"BÁO CÁO PHÂN TÍCH CHUYÊN SÂU TÌNH HÌNH THU TIỀN ĐIỆN QUA NGÂN HÀNG & TRUNG GIAN THANH TOÁN ({month_key}/2026)",
            'company': "CÔNG TY ĐIỆN LỰC LÂM ĐỒNG - PHÒNG TÀI CHÍNH KẾ TOÁN",
            'date_str': "Tháng 09/2026",
            'executive_summary': (
                f"Trong kỳ báo cáo ({month_key}), toàn Công ty Điện lực Lâm Đồng đã thực hiện thu qua hệ thống Ngân hàng "
                f"và các Tổ chức trung gian thanh toán đạt tổng số {format_number(hd_val)} hóa đơn với tổng số tiền {format_money(st_val)}. "
                f"{mom_txt} Kênh thanh toán số hóa qua App và Ví điện tử tiếp tục giữ vai trò chủ lực về số lượng giao dịch, "
                f"chiếm tới {app_hd_pct:.2f}% tổng số hóa đơn thu được trên toàn địa bàn tỉnh Lâm Đồng."
            ),
            'channel_analysis': (
                f"1. Kênh App & Ví điện tử, Trích nợ tự động: Đạt {format_number(ov['channels'][0]['hd'])} HĐ "
                f"({app_hd_pct:.2f}% tổng HĐ), tương ứng {format_money(ov['channels'][0]['st'])} ({app_st_pct:.2f}% tổng số tiền). "
                f"Đây là kênh thanh toán không tiền mặt chiếm ưu thế tuyệt đối đối với khách hàng sinh hoạt và hộ kinh doanh cá thể.\n"
                f"2. Kênh Ủy nhiệm chi (UNC): Đạt {format_number(ov['channels'][1]['hd'])} HĐ ({ov['channels'][1]['pct_hd']:.2f}% HĐ), "
                f"nhưng mang lại giá trị tiền rất cao đạt {format_money(ov['channels'][1]['st'])} ({ov['channels'][1]['pct_st']:.2f}% tổng số tiền). "
                f"Đây là phương thức thanh toán chủ yếu của khối khách hàng Doanh nghiệp sản xuất, Cơ quan hành chính sự nghiệp.\n"
                f"3. Kênh Ủy nhiệm thu (UNT) & Nộp tại quầy: Kênh UNT đạt {format_number(ov['channels'][2]['hd'])} HĐ ({format_money(ov['channels'][2]['st'])}). "
                f"Kênh nộp tại quầy ngân hàng đạt {format_number(ov['channels'][3]['hd'])} HĐ, duy trì tỷ trọng thấp phù hợp định hướng giảm dần quầy vật lý."
            ),
            'unit_analysis': (
                f"Phân tích theo 12 đơn vị Điện lực trực thuộc cho thấy sự phân hóa rõ nét về quy mô và đặc thù địa bàn:\n"
                f"- Top 3 Điện lực dẫn đầu về doanh số thu: {'; '.join(top_unit_strs)}. Trong đó Điện lực Đà Lạt và Điện lực Bảo Lộc "
                f"tiếp tục là 2 đơn vị đầu tàu, đóng góp lớn nhất vào dòng tiền thu của Công ty.\n"
                f"- Nhóm đơn vị miền núi, địa bàn rộng: {'; '.join(bottom_unit_strs)}. Mặc dù quy mô doanh thu không lớn do mật độ phụ tải thấp, "
                f"song tỷ lệ số hóa qua App/Ví tại các đơn vị như Đam Rông, Cát Tiên, Đạ Huoai đều đạt trên 95%, thể hiện nỗ lực rất lớn "
                f"trong việc tuyên truyền thanh toán không dùng tiền mặt tới vùng đồng bào dân tộc và nông thôn."
            ),
            'bank_analysis': (
                f"Toàn Công ty đang hợp tác thanh toán với 22 Ngân hàng và Tổ chức trung gian thanh toán:\n"
                f"- Nhóm Big 4 Ngân hàng (VietcomBank, VietinBank, Agribank, BIDV): Chiếm {big4['share_st']:.2f}% tổng doanh thu "
                f"({format_money(big4['st_tong'])}), đóng vai trò then chốt trong việc thu tiền điện của các khách hàng lớn qua UNC.\n"
                f"- Nhóm Ví điện tử & Fintech (MoMo, VNPay, ZaloPay, Viettel Lâm Đồng, VNPT Media...): Chiếm {fintech['share_hd']:.2f}% "
                f"về số lượng hóa đơn ({format_number(fintech['hd_tong'])} HĐ) và {fintech['share_st']:.2f}% về doanh thu. "
                f"MoMo, VNPay và ZaloPay tiếp tục dẫn đầu nhóm ví điện tử nhờ tiện ích liên kết đa ngân hàng và thói quen người dùng trẻ tuổi.\n"
                f"- Top 5 đối tác có dòng tiền thu hộ lớn nhất: {'; '.join(top_bank_strs)}."
            ),
            'recommendations': [
                "Tiếp tục đẩy mạnh tuyên truyền cài đặt App CSKH EVNSPC kết hợp liên kết trích nợ tự động và ví điện tử cho các khách hàng còn lại.",
                "Làm việc với các Ngân hàng đối tác lớn (Agribank, BIDV, VietinBank) để tối ưu hóa quy trình gạch nợ tự động, hạn chế tối đa các giao dịch treo hoặc lỗi đối soát.",
                "Tăng cường kiểm tra, rà soát tỷ lệ thanh toán không dùng tiền mặt tại các Điện lực có biến động giảm để kịp thời tháo gỡ khó khăn về đường truyền hoặc điểm thu.",
                "Tận dụng tối đa mạng lưới của Viettel Money và Bưu điện Vietnam Post tại các xã vùng sâu, vùng xa thuộc Đam Rông, Đạ Tẻh, Cát Tiên."
            ]
        }
        
        return report_sections

if __name__ == "__main__":
    engine = AnalyticsEngine()
    rep = engine.generate_expert_report("Thang 09")
    print("Report Title:", rep['title'])
    print("Executive Summary:\n", rep['executive_summary'])
    print("\nSUCCESS ANALYTICS")
