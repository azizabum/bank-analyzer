#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محلل كشوف الحساب البنكية - الملف المدموج النهائي
واجهة ويب مع تحليل متقدم ونظام التصنيف ثنائي المستوى + ngrok
يدعم البنك الأهلي وبنك الراجحي
"""

# ==================== المكتبات والاستيرادات ====================
from flask import Flask, render_template, request, jsonify, send_file, url_for, redirect
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime, timedelta
import tempfile
import shutil
from threading import Timer
import logging
import re
from collections import defaultdict
import numpy as np
import subprocess
import time
import requests
import sys
import codecs

# مكتبات معالجة PDF
import pdfplumber
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

# مكتبات معالجة النصوص العربية
import arabic_reshaper
from bidi.algorithm import get_display

# استيراد نظام التصنيف
from expense_categories import (
    classify_transaction,
    get_category_statistics,
    format_category_report,
    EXPENSE_CATEGORIES,
    classify_alrajhi_transaction  # إضافة هذا إذا كان موجوداً في expense_categories
)

# ==================== دوال ngrok وتشغيل الخادم ====================

# إصلاح مشكلة الترميز في Windows
if sys.platform.startswith('win'):
    try:
        os.system('chcp 65001 > nul')
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except:
        pass

def safe_print(text):
    """طباعة آمنة تتجنب أخطاء الترميز"""
    try:
        print(text)
    except UnicodeEncodeError:
        safe_text = text.encode('ascii', 'replace').decode('ascii')
        print(safe_text)

def get_ngrok_url():
    """الحصول على رابط ngrok"""
    try:
        time.sleep(3)
        response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
        tunnels = response.json()['tunnels']

        for tunnel in tunnels:
            if tunnel['proto'] == 'https':
                return tunnel['public_url']
        return None
    except:
        return None

def start_ngrok():
    """تشغيل ngrok"""
    try:
        subprocess.Popen(['ngrok', 'http', '5000'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        safe_print("❌ ngrok غير مثبت!")
        safe_print("💡 ثبت ngrok من: https://ngrok.com/download")
        safe_print("   أو استخدم: npm install -g ngrok")
        return False

def start_with_ngrok():
    """تشغيل التطبيق مع ngrok"""
    safe_print("🚀 تشغيل محلل كشف الحساب مع ngrok...")
    safe_print("⚡ لحل مشكلة الرابط الأزرق في واتساب")
    safe_print("=" * 50)

    # تشغيل ngrok في الخلفية
    safe_print("🔄 تشغيل ngrok...")
    if not start_ngrok():
        return False

    # انتظار والحصول على الرابط
    safe_print("⏳ جاري الحصول على الرابط الخارجي...")

    ngrok_url = None
    for attempt in range(10):
        ngrok_url = get_ngrok_url()
        if ngrok_url:
            break
        time.sleep(1)
        safe_print(f"   محاولة {attempt + 1}/10...")

    if ngrok_url:
        os.environ['EXTERNAL_URL'] = ngrok_url
        safe_print(f"✅ الرابط الخارجي جاهز: {ngrok_url}")
        safe_print("🔵 الروابط الآن ستكون زرقاء وقابلة للضغط في واتساب!")
    else:
        safe_print("⚠️ فشل في الحصول على رابط ngrok")
        safe_print("🔍 سيتم استخدام الرابط المحلي")

    safe_print("\n📱 معلومات المشاركة:")
    safe_print(f"🏠 محلي:  http://localhost:5000")
    if ngrok_url:
        safe_print(f"🌐 خارجي: {ngrok_url}")
        safe_print("✅ شارك الروابط من الرابط الخارجي للحصول على روابط زرقاء!")

    safe_print("\n" + "=" * 50)
    safe_print("🏃‍♂️ بدء التطبيق...")
    
    return True

# ==================== إعداد التطبيق ====================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32 MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

# قاموس لحفظ الروابط النشطة
active_links = {}

# إعداد logging
logging.basicConfig(level=logging.INFO)

# السماح بملفات PDF فقط
ALLOWED_EXTENSIONS = {'pdf'}

# ==================== دوال معالجة النصوص ====================

def fix_arabic_text_advanced(text):
    """إصلاح متقدم للنصوص العربية المستخرجة من PDF"""
    if not text:
        return ""
    
    text = str(text).strip()
    
    # إزالة أحرف التحكم
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    text = re.sub(r'[\u200B-\u200F\u202A-\u202E\u2066-\u2069]', '', text)
    
    # معالجة النص المعكوس
    if is_text_reversed(text):
        text = reverse_mixed_text(text)
    
    # إصلاح الأحرف العربية المنفصلة
    text = fix_separated_arabic_chars(text)
    
    # تطبيع الأرقام
    text = normalize_numbers(text)
    
    # استخدام arabic_reshaper
    try:
        configuration = {
            'delete_harakat': False,
            'shift_harakat_position': True,
            'support_ligatures': True,
            'use_unshaped_instead_of_isolated': False
        }
        reshaper = arabic_reshaper.ArabicReshaper(configuration=configuration)
        reshaped = reshaper.reshape(text)
        text = get_display(reshaped)
    except:
        text = manual_arabic_fix(text)
    
    # تنظيف نهائي
    text = final_cleanup(text)
    
    return text

def is_text_reversed(text):
    """التحقق من أن النص معكوس"""
    patterns = [
        r'^[A-Za-z\s\d]+[\u0600-\u06FF]',
        r'[\u0600-\u06FF]\s*\d+\s*$',
        r'^\d{2}[-/]\d{2}[-/]\d{4}.*[\u0600-\u06FF]',
    ]
    
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    
    reversed_words = ['لاير', 'يدوعس', 'تيوك', 'رطق', 'نيرحب']
    for word in reversed_words:
        if word in text:
            return True
    
    return False

def reverse_mixed_text(text):
    """عكس النص المختلط بذكاء"""
    parts = []
    current = []
    current_type = None
    
    for char in text:
        if '\u0600' <= char <= '\u06FF':
            char_type = 'arabic'
        elif char.isdigit():
            char_type = 'digit'
        elif char.isalpha():
            char_type = 'english'
        else:
            char_type = 'other'
        
        if current_type != char_type:
            if current:
                if current_type == 'arabic':
                    parts.append(''.join(reversed(current)))
                else:
                    parts.append(''.join(current))
                current = []
            current_type = char_type
        
        current.append(char)
    
    if current:
        if current_type == 'arabic':
            parts.append(''.join(reversed(current)))
        else:
            parts.append(''.join(current))
    
    return ' '.join(parts)

def fix_separated_arabic_chars(text):
    """إصلاح الأحرف العربية المنفصلة"""
    text = re.sub(r'([\u0600-\u06FF])\s+([\u0600-\u06FF])', r'\1\2', text)
    
    replacements = {
        'ا ل': 'ال',
        'و ا': 'وا',
        'ي ا': 'يا',
        'ه ا': 'ها',
        'م ن': 'من',
        'ف ي': 'في',
        'إ ل ى': 'إلى',
        'ع ل ى': 'على',
        'ه ذ ا': 'هذا',
        'ه ذ ه': 'هذه',
        'ذ ل ك': 'ذلك',
        'ا ل س ع و د ي': 'السعودي',
        'ا ل ر ي ا ض': 'الرياض',
        'ا ل م م ل ك ة': 'المملكة',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

def normalize_numbers(text):
    """تطبيع الأرقام العربية والهندية"""
    arabic_indic_digits = '٠١٢٣٤٥٦٧٨٩'
    western_digits = '0123456789'
    
    trans_table = str.maketrans(arabic_indic_digits, western_digits)
    text = text.translate(trans_table)
    
    return text

def manual_arabic_fix(text):
    """إصلاح يدوي للنصوص العربية"""
    common_fixes = {
        'ةيدوعسلا': 'السعودية',
        'ضايرلا': 'الرياض',
        'ةدج': 'جدة',
        'ةكم': 'مكة',
        'مامدلا': 'الدمام',
        'ربخلا': 'الخبر',
        'ءارش': 'شراء',
        'عيب': 'بيع',
        'ليوحت': 'تحويل',
        'بحس': 'سحب',
        'عاديإ': 'إيداع',
        'ةيلمع': 'عملية',
        'فارص': 'صراف',
        'يلآ': 'آلي',
        'ةقاطب': 'بطاقة',
        'نامتئا': 'ائتمان',
        'موسر': 'رسوم',
        'ةمدخ': 'خدمة',
        'كنب': 'بنك',
        'يلهلأا': 'الأهلي',
        'باسح': 'حساب',
        'ديصر': 'رصيد',
        'لاير': 'ريال',
        'خيرات': 'تاريخ',
        'غلبم': 'مبلغ',
        'فصو': 'وصف',
    }
    
    for wrong, correct in common_fixes.items():
        text = text.replace(wrong, correct)
    
    return text

def final_cleanup(text):
    """التنظيف النهائي للنص"""
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    text = re.sub(r'\s+([.,،؛:])', r'\1', text)
    text = re.sub(r'([.,،؛:])\s*', r'\1 ', text)
    
    return text

def fix_dots_text(text):
    """إصلاح النصوص التي تظهر كنقاط"""
    if not text:
        return ""
    
    if all(c in '...•․‥…⋯⋮⋰⋱' or ord(c) > 65000 for c in str(text).strip()):
        return "[نص غير مقروء]"
    
    return text

def extract_text_properly(cell_text):
    """استخراج النص بشكل صحيح من خلية PDF"""
    if not cell_text:
        return ""
    
    text = str(cell_text)
    
    if text.strip() in ['...', '***', '•••', '']:
        return "[محتوى مخفي]"
    
    try:
        if '\\x' in repr(text) or '\\u' in repr(text):
            text = text.encode('latin-1').decode('utf-8', errors='ignore')
    except:
        pass
    
    return text

def deep_fix_arabic_text(text):
    """إصلاح عميق للنصوص العربية المعقدة"""
    if not text or text == "[نص غير مقروء]" or text == "[محتوى مخفي]":
        return text
    
    text = str(text).strip()
    
    # معالجة الترميزات الخاطئة
    encodings = ['utf-8', 'windows-1256', 'iso-8859-6', 'cp720', 'cp1256']
    for encoding in encodings:
        try:
            fixed = text.encode('latin-1').decode(encoding)
            if any('\u0600' <= c <= '\u06FF' for c in fixed):
                text = fixed
                break
        except:
            continue
    
    # معالجة المسافات والفواصل
    text = fix_arabic_spacing(text)
    
    # إصلاح الحروف المنفصلة
    text = join_arabic_letters(text)
    
    # معالجة reshaper
    try:
        configuration = {
            'delete_harakat': False,
            'shift_harakat_position': True,
            'support_ligatures': True,
            'language': 'Arabic'
        }
        reshaper = arabic_reshaper.ArabicReshaper(configuration=configuration)
        text = reshaper.reshape(text)
        text = get_display(text)
    except:
        pass
    
    # إصلاح كلمات بنكية شائعة
    text = fix_common_banking_words(text)
    
    return text

def fix_arabic_spacing(text):
    """إصلاح المسافات في النص العربي"""
    text = re.sub(r'([\u0600-\u06FF])\s+([\u0600-\u06FF])', r'\1\2', text)
    text = re.sub(r'ا\s+ل\s*', 'ال', text)
    return text

def join_arabic_letters(text):
    """ربط الحروف العربية المنفصلة"""
    letter_fixes = {
        'ا ل س ع و د ي': 'السعودي',
        'ا ل س ع و د ي ة': 'السعودية',
        'ا ل أ ه ل ي': 'الأهلي',
        'ا ل ب ن ك': 'البنك',
        'ا ل ر ي ا ض': 'الرياض',
        'ت ح و ي ل': 'تحويل',
        'س ح ب': 'سحب',
        'إ ي د ا ع': 'إيداع',
        'ع م ل ي ة': 'عملية',
        'ر ي ا ل': 'ريال',
        'ح س ا ب': 'حساب',
        'ر ص ي د': 'رصيد',
        'ص ر ا ف': 'صراف',
        'آ ل ي': 'آلي',
        'ب ط ا ق ة': 'بطاقة',
        'ا ئ ت م ا ن': 'ائتمان',
        'ر س و م': 'رسوم',
        'خ د م ة': 'خدمة',
        'م ب ل غ': 'مبلغ',
        'ت ا ر ي خ': 'تاريخ',
        'و ص ف': 'وصف',
        'ش ر ا ء': 'شراء',
        'ب ي ع': 'بيع',
        'د ف ع': 'دفع',
        'ن ق د ي': 'نقدي',
        'ش ي ك': 'شيك',
        'ف ا ت و ر ة': 'فاتورة',
        'م د ف و ع ا ت': 'مدفوعات',
        'م ص ر و ف ا ت': 'مصروفات',
        'إ ي ر ا د ا ت': 'إيرادات',
    }
    
    for separated, joined in letter_fixes.items():
        text = text.replace(separated, joined)
    
    return text

def fix_common_banking_words(text):
    """إصلاح الكلمات البنكية الشائعة"""
    banking_fixes = {
        'يلهلأا كنبلا': 'البنك الأهلي',
        'يلهلاا كنبلا': 'البنك الأهلي',
        'يدوعسلا يلهلأا': 'الأهلي السعودي',
        'يدوعسلا يلهلاا': 'الأهلي السعودي',
        'كنبلا يلهلأا': 'البنك الأهلي',
        'كنبلا يلهلاا': 'البنك الأهلي',
        'ضايرلا': 'الرياض',
        'ةدج': 'جدة',
        'ةكم': 'مكة',
        'ةنيدملا': 'المدينة',
        'مامدلا': 'الدمام',
        'ربخلا': 'الخبر',
        'فئاطلا': 'الطائف',
        'ليبجلا': 'الجبيل',
        'جرخلا': 'الخرج',
        'ليوحت': 'تحويل',
        'بحس': 'سحب',
        'عاديإ': 'إيداع',
        'ةيلمع': 'عملية',
        'دادس': 'سداد',
        'عفد': 'دفع',
        'ءارش': 'شراء',
        'عيب': 'بيع',
        'ضرق': 'قرض',
        'ليومت': 'تمويل',
        'لاير': 'ريال',
        'يدوعس لاير': 'ريال سعودي',
        'غلبم': 'مبلغ',
        'ديصر': 'رصيد',
        'باسح': 'حساب',
        'يراج باسح': 'حساب جاري',
        'رخدم باسح': 'حساب مدخر',
        'ةقاطب': 'بطاقة',
        'نامتئا ةقاطب': 'بطاقة ائتمان',
        'فارص': 'صراف',
        'يلآ فارص': 'صراف آلي',
        'موسر': 'رسوم',
        'ةبيرض': 'ضريبة',
        'ةمدخ موسر': 'رسوم خدمة',
        'ةفاضملا ةميقلا ةبيرض': 'ضريبة القيمة المضافة',
        'خيرات': 'تاريخ',
        'فصو': 'وصف',
        'عجرم': 'مرجع',
        'مقر': 'رقم',
        'ةروتاف': 'فاتورة',
        'لاصيإ': 'إيصال',
        'دقن': 'نقد',
        'يدقن': 'نقدي',
        'كيش': 'شيك',
    }
    
    for wrong, correct in banking_fixes.items():
        text = text.replace(wrong, correct)
    
    return text

# ==================== دوال التنظيف والتصنيف ====================

def clean_description(desc):
    """تنظيف وصف العملية"""
    if not desc:
        return ""
    
    desc = fix_dots_text(desc)
    
    if desc in ["[نص غير مقروء]", "[محتوى مخفي]"]:
        return "عملية مصرفية"
    
    desc = desc.strip()
    
    # إزالة الأنماط غير المرغوبة
    desc = re.sub(r"MCC[:\-]?\d{4}", "", desc, flags=re.IGNORECASE)
    desc = re.sub(r"VAT\s*CHRG.*", "", desc, flags=re.IGNORECASE)
    desc = re.sub(r"Charges:.*", "", desc, flags=re.IGNORECASE)
    desc = re.sub(r"CITY[:\-]?.*?(?=\s|$)", "", desc, flags=re.IGNORECASE)
    desc = re.sub(r"MADA\s+\*{2,}\d+", "", desc, flags=re.IGNORECASE)
    desc = re.sub(r"CHNL:.*?DEP", "", desc, flags=re.IGNORECASE)
    desc = re.sub(r"Payment Systems.*?DEP", "", desc, flags=re.IGNORECASE)
    desc = re.sub(r"ID:\s*\d+", "", desc, flags=re.IGNORECASE)
    desc = re.sub(r"DEP\s+\d+", "", desc, flags=re.IGNORECASE)
    desc = re.sub(r"\*{4,}\d{4}", "", desc)
    desc = re.sub(r"\b\d{10,}\b", "", desc)
    
    # تنظيف المسافات
    desc = re.sub(r"\s{2,}", " ", desc)
    desc = desc.strip()
    
    if not desc or len(desc) < 3:
        return "عملية مصرفية"
    
    return desc

def classify_expense_enhanced(desc, mcc=None, bank=None):
    """تصنيف المصروف باستخدام النظام الجديد ثنائي المستوى"""
    if not desc:
        return "❓ غير مصنف"
    
    # تحقق من نوع البنك وإذا كان الراجحي استخدم دالة خاصة
    if bank == 'الراجحي' and 'classify_alrajhi_transaction' in globals():
        main_category, sub_category = classify_alrajhi_transaction(desc)
    else:
        # استخدام دالة التصنيف العامة
        main_category, sub_category = classify_transaction(desc)
    
    # دمج التصنيف الرئيسي والفرعي
    if sub_category != "غير محدد":
        return f"{main_category} - {sub_category}"
    else:
        return main_category

# ==================== دوال الحسابات المالية ====================

def calculate_expense_percentages(expense_details):
    """حساب نسب المصاريف"""
    total_expenses = sum(
        sum(trans['amount'] for trans in transactions)
        for transactions in expense_details.values()
    )
    
    percentages = {}
    for category, transactions in expense_details.items():
        category_total = sum(trans['amount'] for trans in transactions)
        percentages[category] = {
            'amount': category_total,
            'percentage': (category_total / total_expenses * 100) if total_expenses > 0 else 0,
            'count': len(transactions)
        }
    
    return percentages

def calculate_financial_metrics(income_details, expense_details):
    """حساب المؤشرات المالية"""
    # حساب المصاريف
    all_expenses = []
    for transactions in expense_details.values():
        all_expenses.extend([trans['amount'] for trans in transactions])
    
    # حساب الدخل
    all_incomes = [trans['amount'] for trans in income_details]
    
    metrics = {
        'avg_daily_expense': sum(all_expenses) / 30 if all_expenses else 0,
        'max_expense': max(all_expenses) if all_expenses else 0,
        'min_expense': min(all_expenses) if all_expenses else 0,
        'avg_income': sum(all_incomes) / len(all_incomes) if all_incomes else 0,
        'max_income': max(all_incomes) if all_incomes else 0,
        'min_income': min(all_incomes) if all_incomes else 0,
        'total_transactions': len(all_expenses) + len(all_incomes)
    }
    
    return metrics

def generate_insights(total_income, total_expenses, expense_details, financial_metrics):
    """توليد رؤى ذكية وتوصيات واقعية مبنية على البيانات الفعلية"""
    insights = []
    
    # حساب المؤشرات الأساسية
    net_balance = total_income - total_expenses
    savings_rate = ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0
    expense_ratio = (total_expenses / total_income * 100) if total_income > 0 else 0
    daily_expense = financial_metrics.get('avg_daily_expense', 0)
    
    # 1. تحليل الوضع المالي العام
    if net_balance > 0:
        if savings_rate >= 20:
            insights.append({
                'title': '💰 أداء مالي ممتاز',
                'description': f'معدل الادخار {savings_rate:.1f}% من دخلك - أنت في المسار الصحيح',
                'potential_saving': 0
            })
        elif savings_rate >= 10:
            insights.append({
                'title': '👍 أداء مالي جيد',
                'description': f'تدخر {savings_rate:.1f}% من دخلك، حاول الوصول لـ 20%',
                'potential_saving': (total_income * 0.2) - (total_income - total_expenses)
            })
        else:
            insights.append({
                'title': '⚠️ ادخار منخفض',
                'description': f'تدخر فقط {savings_rate:.1f}% من دخلك، الهدف الأمثل 20%',
                'potential_saving': (total_income * 0.2) - (total_income - total_expenses)
            })
    else:
        deficit = abs(net_balance)
        insights.append({
            'title': '🚨 تحذير: مصاريفك تتجاوز دخلك',
            'description': f'العجز الشهري {deficit:,.0f} ريال - يجب تقليل المصاريف فوراً',
            'potential_saving': deficit
        })
    
    # 2. تحليل الفئات الأكثر إنفاقاً
    if expense_details:
        # ترتيب الفئات حسب المبلغ
        sorted_categories = sorted(
            [(cat, sum(t['amount'] for t in trans)) for cat, trans in expense_details.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        # أكبر فئة إنفاق
        if sorted_categories:
            top_category, top_amount = sorted_categories[0]
            top_percentage = (top_amount / total_expenses * 100)
            
            # تنظيف اسم الفئة من الإيموجي
            clean_category = re.sub(r'[^\w\s\-]', '', top_category).strip()
            
            if top_percentage > 30:
                insights.append({
                    'title': f'📊 {clean_category} يستنزف ميزانيتك',
                    'description': f'هذه الفئة تشكل {top_percentage:.0f}% من مصاريفك ({top_amount:,.0f} ريال) - راجع ضرورة كل عملية',
                    'potential_saving': top_amount * 0.2  # توفير 20% من هذه الفئة
                })
            
            # البحث عن فئات يمكن تقليلها
            for category, amount in sorted_categories[1:4]:  # التحقق من أعلى 4 فئات
                percentage = (amount / total_expenses * 100)
                clean_cat = re.sub(r'[^\w\s\-]', '', category).strip()
                
                # تحديد الفئات القابلة للتقليل
                reducible_categories = ['مطاعم', 'كافيهات', 'ترفيه', 'تسوق', 'ملابس', 'اشتراكات']
                if any(cat in clean_cat for cat in reducible_categories) and percentage > 15:
                    insights.append({
                        'title': f'💡 فرصة توفير في {clean_cat}',
                        'description': f'تنفق {percentage:.0f}% ({amount:,.0f} ريال) - جرب تقليلها بـ 30%',
                        'potential_saving': amount * 0.3
                    })
                    break
    
    # 3. تحليل متوسط الإنفاق اليومي
    if daily_expense > 0:
        daily_income = total_income / 30
        daily_ratio = (daily_expense / daily_income * 100) if daily_income > 0 else 0
        
        if daily_ratio > 90:
            insights.append({
                'title': '📅 إنفاقك اليومي مرتفع جداً',
                'description': f'تنفق {daily_expense:,.0f} ريال يومياً ({daily_ratio:.0f}% من دخلك اليومي) - حدد ميزانية يومية واضحة',
                'potential_saving': (daily_expense - (daily_income * 0.7)) * 30
            })
    
    # 4. تحليل عدد العمليات
    total_transactions = sum(len(trans) for trans in expense_details.values())
    if total_transactions > 0:
        avg_transaction = total_expenses / total_transactions
        
        if total_transactions > 100:
            insights.append({
                'title': '🔄 عدد عمليات مرتفع',
                'description': f'{total_transactions} عملية شهرياً (متوسط {avg_transaction:,.0f} ريال) - حاول تجميع المشتريات',
                'potential_saving': 0
            })
    
    # 5. تحليل التحويلات المالية
    for category, transactions in expense_details.items():
        if 'تحويلات' in category:
            transfer_amount = sum(t['amount'] for t in transactions)
            transfer_percentage = (transfer_amount / total_expenses * 100)
            
            if transfer_percentage > 40:
                insights.append({
                    'title': '🔄 التحويلات المالية مرتفعة',
                    'description': f'تشكل {transfer_percentage:.0f}% من مصاريفك - تأكد من ضرورة كل تحويل',
                    'potential_saving': transfer_amount * 0.1
                })
                break
    
    # 6. نصيحة الادخار التلقائي
    if savings_rate < 10 and total_income > 0:
        recommended_savings = total_income * 0.1  # 10% من الدخل
        insights.append({
            'title': '💰 ابدأ الادخار التلقائي',
            'description': f'خصص {recommended_savings:,.0f} ريال شهرياً (10% من دخلك) للادخار واجعله تحويل تلقائي',
            'potential_saving': 0
        })
    
    # 7. البحث عن أنماط الإنفاق المتكررة
    for category, transactions in expense_details.items():
        if len(transactions) >= 10:  # فئات بعمليات متكررة
            clean_cat = re.sub(r'[^\w\s\-]', '', category).strip()
            category_amount = sum(t['amount'] for t in transactions)
            avg_per_transaction = category_amount / len(transactions)
            
            if 'قهوة' in clean_cat or 'كافي' in clean_cat:
                daily_coffee = len(transactions) / 30
                if daily_coffee > 0.5:  # أكثر من مرة كل يومين
                    monthly_coffee_cost = category_amount
                    insights.append({
                        'title': '☕ عادة القهوة اليومية',
                        'description': f'تشرب قهوة {daily_coffee:.1f} مرة يومياً بتكلفة {monthly_coffee_cost:,.0f} ريال شهرياً - جرب تقليلها للنصف',
                        'potential_saving': monthly_coffee_cost * 0.5
                    })
                    break
    
    # ترتيب الرؤى حسب الأولوية
    insights.sort(key=lambda x: x.get('potential_saving', 0), reverse=True)
    
    # إرجاع أهم 5 رؤى فقط
    return insights[:5]

# ==================== دوال استخراج البيانات ====================

def detect_bank_type(pdf_path):
    """كشف نوع البنك من محتوى PDF"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # فحص أول 3 صفحات للتأكد
            pages_to_check = min(3, len(pdf.pages))
            combined_text = ""
            
            for i in range(pages_to_check):
                page_text = pdf.pages[i].extract_text() or ""
                combined_text += page_text + " "
            
            combined_text_lower = combined_text.lower()
            
            # تحسين كشف بنك الراجحي - إضافة المؤشرات الصحيحة
            rajhi_indicators = [
                'alrajhibank.com', 'alrajhibank.com.sa',  # الموقع الرسمي
                'alrajhi bank', 'مصرف الراجحي',
                '920 003 344',  # رقم الهاتف المميز للراجحي
                'الراجحي', 'alrajhi', 'al rajhi', 'al-rajhi',
                'مصرف الراجحي', 'al rajhi bank', 'الراجحي المصرفية',
                'alrajhi banking', 'مصرف الراجحي المصرفية',
                'al rajhi banking', 'شركة الراجحي المصرفية',
                'rajhi', 'الراجحى', 'al-rajhi bank',
                'مصرف الراجحى', 'alrajhi bank',
                # إضافة أرقام وأكواد خاصة بالراجحي
                '80000', 'rjhi', 'sarb', 'الراجحي للاستثمار',
                'al rajhi capital', 'الراجحي كابيتال'
            ]
            
            # التحقق من مؤشرات الراجحي
            for indicator in rajhi_indicators:
                if indicator in combined_text_lower:
                    app.logger.info(f"✅ تم اكتشاف بنك الراجحي بواسطة: {indicator}")
                    return 'الراجحي'
            
            # كشف البنك الأهلي
            ahli_indicators = [
                'الأهلي', 'الاهلي', 'ahli', 'al ahli', 'البنك الأهلي',
                'البنك الاهلي', 'national bank', 'snb', 'الأهلي السعودي',
                'البنك الأهلي السعودي', 'saudi national bank',
                'البنك الاهلي التجاري', 'ncb', 'الاهلي التجاري'
            ]
            
            for indicator in ahli_indicators:
                if indicator in combined_text_lower:
                    app.logger.info(f"✅ تم اكتشاف البنك الأهلي بواسطة: {indicator}")
                    return 'الأهلي'
            
            # البحث عن أنماط خاصة في تنسيق الكشف
            # الراجحي يستخدم جدول بتنسيق: التاريخ | تفاصيل العملية | مدين | دائن | الرصيد
            if 'تفاصيل العملية' in combined_text and 'مدين' in combined_text and 'دائن' in combined_text and 'الرصيد' in combined_text:
                # التحقق من وجود "Statement Details" و "تفاصيل الكشف" معاً (خاص بالراجحي)
                if 'statement details' in combined_text_lower and 'تفاصيل الكشف' in combined_text:
                    app.logger.info("✅ تم اكتشاف بنك الراجحي من خلال تنسيق الكشف الثنائي اللغة")
                    return 'الراجحي'
            
            # محاولة أخرى: البحث عن أنماط خاصة بكل بنك في الجداول
            for page in pdf.pages[:pages_to_check]:
                tables = page.extract_tables()
                for table in tables:
                    if not table:
                        continue
                    
                    # فحص رأس الجدول
                    if len(table) > 0:
                        header_row = ' '.join(str(cell) for cell in table[0] if cell).lower()
                        
                        # نمط الراجحي: التاريخ | تفاصيل العملية | مدين | دائن | الرصيد
                        if all(word in header_row for word in ['تاريخ', 'تفاصيل', 'مدين', 'دائن', 'رصيد']):
                            app.logger.info("✅ تم اكتشاف بنك الراجحي من خلال تنسيق رأس الجدول")
                            return 'الراجحي'
                        
                        # نمط الأهلي: يختلف عن الراجحي
                        if 'transaction' in header_row and 'description' in header_row:
                            app.logger.info("✅ تم اكتشاف البنك الأهلي من خلال تنسيق رأس الجدول")
                            return 'الأهلي'
                
    except Exception as e:
        app.logger.error(f"❌ خطأ في كشف نوع البنك: {str(e)}")
    
    app.logger.warning("⚠️ لم يتم التعرف على نوع البنك")
    return 'غير محدد'


def extract_transaction_from_line(line):
    """استخراج معاملة من سطر نصي"""
    date_pattern = r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
    amount_pattern = r'([\d,]+\.?\d*)'
    
    date_match = re.search(date_pattern, line)
    amount_matches = re.findall(amount_pattern, line)
    
    if date_match and amount_matches:
        date = date_match.group(1)
        amount = amount_matches[-1].replace(',', '')
        
        desc_start = date_match.end()
        desc_end = line.rfind(amount_matches[-1])
        
        if desc_end > desc_start:
            desc = line[desc_start:desc_end].strip()
            return [date, desc, amount]
    
    return None

def extract_with_pymupdf(pdf_path):
    """استخراج النصوص باستخدام PyMuPDF"""
    if not PYMUPDF_AVAILABLE:
        return None
    
    try:
        doc = fitz.open(pdf_path)
        all_data = []
        
        # كشف نوع البنك
        bank_type = detect_bank_type(pdf_path)
        app.logger.info(f"🏦 PyMuPDF: نوع البنك = {bank_type}")
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # محاولة استخراج الجداول
            tables = page.find_tables()
            
            if tables:
                for table in tables:
                    table_data = table.extract()
                    
                    # تخطي الصف الأول إذا كان عناوين
                    start_row = 0
                    if table_data and len(table_data) > 0:
                        first_row_text = ' '.join(str(cell) for cell in table_data[0] if cell).lower()
                        if any(header in first_row_text for header in ['تاريخ', 'date', 'مدين', 'دائن', 'الرصيد', 'تفاصيل']):
                            start_row = 1
                    
                    for row_idx in range(start_row, len(table_data)):
                        row = table_data[row_idx]
                        if not row or len(row) < 4:
                            continue
                        
                        if bank_type == 'الراجحي':
                            # معالجة خاصة للراجحي
                            transaction = extract_alrajhi_transaction(row)
                            if transaction:
                                all_data.append({
                                    'date': transaction['date'],
                                    'desc': transaction['desc'],
                                    'amount': transaction['amount'],
                                    'type': transaction['type']
                                })
                        else:
                            # معالجة للبنوك الأخرى
                            if len(row) >= 3:
                                all_data.append({
                                    'date': fix_arabic_text_advanced(str(row[0])),
                                    'desc': fix_arabic_text_advanced(str(row[1])),
                                    'amount': str(row[2]) if len(row) > 2 else ''
                                })
            else:
                # إذا لم توجد جداول، استخرج من النص
                text = page.get_text()
                lines = text.split('\n')
                
                # البحث عن نمط المعاملات في النص
                in_transaction_section = False
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # بداية قسم المعاملات
                    if 'التاريخ' in line and 'تفاصيل العملية' in line:
                        in_transaction_section = True
                        continue
                    
                    if in_transaction_section:
                        # محاولة استخراج معاملة من السطر
                        # نمط التاريخ
                        date_match = re.search(r'(\d{4}/\d{2}/\d{2})', line)
                        if date_match:
                            # جمع الأسطر التالية للحصول على التفاصيل الكاملة
                            transaction_lines = [line]
                            
                            # جمع الأسطر التالية حتى نجد تاريخ جديد أو نهاية
                            j = i + 1
                            while j < len(lines) and not re.search(r'^\d{4}/\d{2}/\d{2}', lines[j]):
                                if lines[j].strip():
                                    transaction_lines.append(lines[j].strip())
                                j += 1
                                if j - i > 5:  # حد أقصى 5 أسطر للمعاملة الواحدة
                                    break
                            
                            # دمج الأسطر
                            full_transaction = ' '.join(transaction_lines)
                            
                            # استخراج المبلغ
                            amount_match = re.search(r'([\d,]+\.?\d*)\s*SAR', full_transaction)
                            if amount_match:
                                try:
                                    amount_str = amount_match.group(1).replace(',', '')
                                    amount = float(amount_str)
                                    
                                    # تحديد نوع المعاملة
                                    if 'دائن' in full_transaction or 'حوالة واردة' in full_transaction:
                                        transaction_type = 'income'
                                    else:
                                        transaction_type = 'expense'
                                        amount = -amount
                                    
                                    # استخراج التفاصيل
                                    desc_start = full_transaction.find('SAR') + 3
                                    desc = full_transaction[desc_start:].strip()
                                    
                                    if not desc:
                                        # محاولة استخراج من مكان آخر
                                        desc_parts = full_transaction.split('SAR')
                                        if len(desc_parts) > 1:
                                            desc = desc_parts[-1].strip()
                                    
                                    all_data.append({
                                        'date': date_match.group(1),
                                        'desc': fix_arabic_text_advanced(desc) if desc else "عملية بنكية",
                                        'amount': amount,
                                        'type': transaction_type
                                    })
                                except:
                                    continue
        
        doc.close()
        
        app.logger.info(f"✅ PyMuPDF: تم استخراج {len(all_data)} معاملة")
        return all_data
        
    except Exception as e:
        app.logger.error(f"❌ خطأ في PyMuPDF: {str(e)}")
        return None
    
def extract_alrajhi_transaction(row, page_text=None):
    """
    استخراج معاملة من كشف حساب الراجحي
    التنسيق المتوقع: تاريخ | تفاصيل العملية | مدين | دائن | الرصيد
    أو: تاريخ | مدين | دائن | الرصيد | تفاصيل العملية
    """
    if not row or len(row) < 4:
        return None
    
    try:
        # تنظيف البيانات أولاً
        cleaned_row = []
        for cell in row:
            cleaned = extract_text_properly(cell)
            if cleaned and cleaned != "[نص غير مقروء]":
                cleaned_row.append(cleaned)
            else:
                cleaned_row.append("")
        
        # إضافة خلايا فارغة إذا كان العدد أقل من 5
        while len(cleaned_row) < 5:
            cleaned_row.append("")
        
        # محاولة تحديد موقع البيانات بذكاء
        date_idx = -1
        details_idx = -1
        debit_idx = -1
        credit_idx = -1
        balance_idx = -1
        
        # البحث عن التاريخ (عادة في العمود الأول)
        for i, cell in enumerate(cleaned_row):
            if re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', cell):
                date_idx = i
                break
        
        # البحث عن المبالغ (تحتوي على أرقام و SAR أو ريال)
        amount_indices = []
        for i, cell in enumerate(cleaned_row):
            if i != date_idx and re.search(r'[\d,]+\.?\d*\s*(SAR|ريال|﷼)?', cell):
                amount_indices.append(i)
        
        # تحديد أماكن المبالغ
        if len(amount_indices) >= 3:
            # نفترض: مدين، دائن، رصيد
            debit_idx = amount_indices[0]
            credit_idx = amount_indices[1]
            balance_idx = amount_indices[2]
        elif len(amount_indices) == 2:
            # قد يكون أحد الحقول فارغ
            debit_idx = amount_indices[0]
            credit_idx = amount_indices[1]
        
        # البحث عن التفاصيل (عادة أطول نص وليس رقم)
        max_len = 0
        for i, cell in enumerate(cleaned_row):
            if i not in [date_idx, debit_idx, credit_idx, balance_idx]:
                if len(cell) > max_len and not re.match(r'^[\d\s,.-]+$', cell):
                    max_len = len(cell)
                    details_idx = i
        
        # إذا لم نجد التفاصيل، نبحث في آخر عمود
        if details_idx == -1 and len(cleaned_row) >= 5:
            for i in [4, 1]:  # جرب العمود الخامس ثم الثاني
                if i not in [debit_idx, credit_idx, balance_idx] and cleaned_row[i]:
                    details_idx = i
                    break
        
        # استخراج البيانات
        date = cleaned_row[date_idx] if date_idx >= 0 else ""
        details = cleaned_row[details_idx] if details_idx >= 0 else ""
        debit = cleaned_row[debit_idx] if debit_idx >= 0 else ""
        credit = cleaned_row[credit_idx] if credit_idx >= 0 else ""
        
        # معالجة المبلغ
        amount = 0.0
        transaction_type = None
        
        # معالجة المبلغ المدين (مصروف)
        if debit and debit not in ["0.00", "0.00 SAR", "0", "-"]:
            amount_str = re.sub(r'[^\d\.-]', '', debit)
            amount_str = amount_str.replace(',', '')
            try:
                amount_val = float(amount_str)
                if amount_val > 0:
                    amount = -amount_val  # سالب للمصروفات
                    transaction_type = "expense"
            except:
                pass
        
        # معالجة المبلغ الدائن (دخل)
        if credit and credit not in ["0.00", "0.00 SAR", "0", "-"]:
            amount_str = re.sub(r'[^\d\.-]', '', credit)
            amount_str = amount_str.replace(',', '')
            try:
                amount_val = float(amount_str)
                if amount_val > 0:
                    amount = amount_val  # موجب للدخل
                    transaction_type = "income"
            except:
                pass
        
        # إذا لم نجد مبلغ، نحاول البحث في كل الخلايا
        if amount == 0:
            for i, cell in enumerate(cleaned_row):
                if i != date_idx and i != details_idx:
                    # البحث عن نمط المبلغ
                    match = re.search(r'([\d,]+\.?\d*)\s*(SAR|ريال|﷼)?', cell)
                    if match:
                        amount_str = match.group(1).replace(',', '')
                        try:
                            amount_val = float(amount_str)
                            if amount_val > 0 and amount_val != 100000:  # تجاهل الأرقام الكبيرة جداً
                                # تحديد نوع العملية بناءً على السياق
                                if any(word in str(row).lower() for word in ['سحب', 'شراء', 'دفع', 'withdrawal', 'purchase']):
                                    amount = -amount_val
                                    transaction_type = "expense"
                                else:
                                    amount = amount_val
                                    transaction_type = "income"
                                break
                        except:
                            pass
        
        # إذا تم العثور على مبلغ صالح
        if amount != 0:
            # تنظيف التاريخ
            if not date or date == "[نص غير مقروء]":
                date = datetime.now().strftime("%d/%m/%Y")
            else:
                date = fix_arabic_text_advanced(date)
            
            # تنظيف وإصلاح تفاصيل العملية
            if not details or details == "[نص غير مقروء]":
                # محاولة إيجاد التفاصيل في أي خلية
                for cell in cleaned_row:
                    if cell and len(cell) > 10 and not re.match(r'^[\d\s,.-]+$', cell) and cell != date:
                        details = cell
                        break
                
                if not details:
                    details = "عملية بنكية - الراجحي"
            
            details = deep_fix_arabic_text(details)
            
            # تسجيل للتتبع
            app.logger.info(f"✅ معاملة الراجحي: التاريخ={date}, المبلغ={amount}, النوع={transaction_type}, التفاصيل={details[:50]}...")
            
            return {
                'date': date,
                'desc': details,
                'amount': amount,
                'type': transaction_type,
                'bank': 'الراجحي'
            }
        else:
            app.logger.warning(f"⚠️ لم يتم العثور على مبلغ صالح في الصف: {cleaned_row}")
    
    except Exception as e:
        app.logger.error(f"❌ خطأ في استخراج معاملة الراجحي: {str(e)}")
        app.logger.error(f"   الصف: {row}")
    
    return None


def extract_alrajhi_transaction_from_data(item):
    """استخراج معاملة الراجحي من البيانات المستخرجة بواسطة PyMuPDF"""
    if isinstance(item, dict):
        # إذا كانت البيانات جاهزة بالفعل
        if all(key in item for key in ['date', 'desc', 'amount']):
            try:
                # التأكد من أن المبلغ رقم
                if isinstance(item['amount'], (int, float)):
                    amount = float(item['amount'])
                else:
                    # محاولة تحويل النص إلى رقم
                    amount_str = re.sub(r'[^\d\.-]', '', str(item['amount']))
                    amount = float(amount_str) if amount_str else 0
                
                # تحديد النوع إذا لم يكن موجود
                if 'type' not in item:
                    item['type'] = 'income' if amount > 0 else 'expense'
                
                return {
                    'date': item['date'],
                    'desc': item['desc'],
                    'amount': amount,
                    'type': item['type'],
                    'bank': 'الراجحي'
                }
            except Exception as e:
                app.logger.error(f"خطأ في معالجة البيانات: {str(e)}")
                return None
    
    # إذا كانت البيانات عبارة عن قائمة
    elif isinstance(item, (list, tuple)):
        return extract_alrajhi_transaction(list(item))
    
    return None

def process_transaction(date, desc, amount, income_details, expense_details):
    """معالجة معاملة واحدة"""
    if amount > 0:
        # دخل
        income_details.append({
            "date": date, 
            "desc": desc, 
            "amount": amount
        })
    else:
        # مصروف
        abs_amt = abs(amount)
        category = classify_expense_enhanced(desc)
        expense_details[category].append({
            "date": date, 
            "desc": desc, 
            "amount": abs_amt
        })

def analyze_transactions(pdf_path):
    """تحليل العمليات من ملف PDF واحد - يدعم البنك الأهلي والراجحي"""
    income_count = 0
    expense_count = 0
    total_income = 0.0
    total_expense = 0.0
    skipped_rows = 0
    total_rows = 0
    income_details = []
    expense_details = defaultdict(list)
    
    app.logger.info("🔍 بدء تحليل كشف الحساب...")
    
    # كشف نوع البنك
    bank_type = detect_bank_type(pdf_path)
    app.logger.info(f"🏦 نوع البنك المكتشف: {bank_type}")

    # محاولة استخدام PyMuPDF أولاً
    if PYMUPDF_AVAILABLE:
        app.logger.info("📘 استخدام PyMuPDF لاستخراج النصوص...")
        extracted_data = extract_with_pymupdf(pdf_path)
        
        if extracted_data:
            for item in extracted_data:
                total_rows += 1
                
                # معالجة حسب نوع البنك
                if bank_type == 'الراجحي':
                    # استخراج معاملة الراجحي
                    transaction = extract_alrajhi_transaction_from_data(item)
                    if transaction:
                        if transaction['type'] == 'income':
                            income_count += 1
                            total_income += abs(transaction['amount'])
                            income_details.append({
                                "date": transaction['date'],
                                "desc": transaction['desc'],
                                "amount": abs(transaction['amount'])
                            })
                        elif transaction['type'] == 'expense':
                            expense_count += 1
                            abs_amt = abs(transaction['amount'])
                            total_expense += abs_amt
                            
                            category = classify_expense_enhanced(transaction['desc'], bank=bank_type)
                            expense_details[category].append({
                                "date": transaction['date'],
                                "desc": transaction['desc'],
                                "amount": abs_amt
                            })
                    else:
                        skipped_rows += 1
                else:
                    # معالجة البنك الأهلي (الطريقة الأصلية)
                    try:
                        amount = float(re.sub(r"[^\d\.-]", "", str(item['amount'])))
                    except:
                        skipped_rows += 1
                        continue
                    
                    date = item['date']
                    desc = item['desc']
                    
                    if not desc or desc == "[نص غير مقروء]":
                        desc = "عملية مصرفية"
                    
                    if amount > 0:
                        if any(x in desc.lower() for x in ["ضريبة", "رسوم", "vat", "fee", "charge"]):
                            skipped_rows += 1
                            continue
                        income_count += 1
                        total_income += amount
                        income_details.append({"date": date, "desc": desc, "amount": amount})
                    elif amount < 0:
                        expense_count += 1
                        abs_amt = abs(amount)
                        total_expense += abs_amt
                        
                        category = classify_expense_enhanced(desc)
                        expense_details[category].append({"date": date, "desc": desc, "amount": abs_amt})
                    else:
                        skipped_rows += 1
            
            total_count = income_count + expense_count
            app.logger.info(f"✅ تم تحليل {total_count} عملية بنجاح!")
            return total_rows, total_count, income_count, total_income, expense_count, total_expense, skipped_rows, income_details, expense_details

    # العودة إلى pdfplumber
    app.logger.info("📄 استخدام pdfplumber...")
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables({
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance": 3,
                "join_tolerance": 3,
                "edge_min_length": 50,
                "min_words_vertical": 0,
                "min_words_horizontal": 0,
                "text_tolerance": 3,
                "text_x_tolerance": 3,
                "text_y_tolerance": 3,
                "intersection_tolerance": 3,
            })
            
            if not tables:
                text = page.extract_text()
                if text:
                    lines = text.split('\n')
                    for line in lines:
                        # معالجة للبنك الأهلي من النص
                        if bank_type != 'الراجحي':
                            parts = extract_transaction_from_line(line)
                            if parts:
                                total_rows += 1
                                date = deep_fix_arabic_text(parts[0])
                                desc = deep_fix_arabic_text(parts[1])
                                try:
                                    amount = float(parts[2])
                                    process_transaction(date, desc, amount, income_details, expense_details)
                                    if amount > 0:
                                        income_count += 1
                                        total_income += amount
                                    else:
                                        expense_count += 1
                                        total_expense += abs(amount)
                                except:
                                    skipped_rows += 1
                continue
            
            for table in tables:
                # تخطي الصف الأول (العناوين)
                for row in table[1:]:
                    total_rows += 1
                    
                    if bank_type == 'الراجحي':
                        # معالجة خاصة لبنك الراجحي
                        transaction = extract_alrajhi_transaction(row)
                        if transaction:
                            if transaction['type'] == 'income':
                                income_count += 1
                                total_income += abs(transaction['amount'])
                                income_details.append({
                                    "date": transaction['date'],
                                    "desc": transaction['desc'],
                                    "amount": abs(transaction['amount'])
                                })
                            elif transaction['type'] == 'expense':
                                expense_count += 1
                                abs_amt = abs(transaction['amount'])
                                total_expense += abs_amt
                                
                                category = classify_expense_enhanced(transaction['desc'], bank=bank_type)
                                expense_details[category].append({
                                    "date": transaction['date'],
                                    "desc": transaction['desc'],
                                    "amount": abs_amt
                                })
                        else:
                            skipped_rows += 1
                    
                    else:
                        # معالجة البنك الأهلي (الطريقة الأصلية)
                        if len(row) < 3 or not row[2]:
                            skipped_rows += 1
                            continue
                        
                        date_raw = extract_text_properly(row[0])
                        desc_raw = extract_text_properly(row[1])
                        amount_raw = extract_text_properly(row[2])
                        
                        date = deep_fix_arabic_text(date_raw)
                        desc = deep_fix_arabic_text(desc_raw)
                        
                        if not date or date == "[نص غير مقروء]":
                            date = datetime.now().strftime("%d/%m/%Y")
                        
                        if not desc or desc == "[نص غير مقروء]":
                            desc = "عملية مصرفية"
                        
                        try:
                            amount = float(re.sub(r"[^\d\.-]", "", amount_raw))
                        except:
                            skipped_rows += 1
                            continue

                        if amount > 0:
                            if any(x in desc.lower() for x in ["ضريبة", "رسوم", "vat", "fee", "charge"]):
                                skipped_rows += 1
                                continue
                            income_count += 1
                            total_income += amount
                            income_details.append({"date": date, "desc": desc, "amount": amount})
                        elif amount < 0:
                            expense_count += 1
                            abs_amt = abs(amount)
                            total_expense += abs_amt
                            
                            category = classify_expense_enhanced(desc)
                            expense_details[category].append({"date": date, "desc": desc, "amount": abs_amt})
                        else:
                            skipped_rows += 1

    total_count = income_count + expense_count
    
    if skipped_rows > total_rows * 0.3:
        app.logger.warning(f"⚠️ تحذير: {skipped_rows} من {total_rows} صف لم يتم قراءتها بشكل صحيح")
        app.logger.info("💡 نصيحة: جرّب تثبيت PyMuPDF للحصول على نتائج أفضل: pip install PyMuPDF")
    
    app.logger.info(f"🏦 تم تحليل كشف حساب {bank_type}")
    app.logger.info(f"📊 إجمالي العمليات: {total_count}")
    app.logger.info(f"📈 الدخل: {income_count} عملية - {total_income:,.2f} ريال")
    app.logger.info(f"📉 المصاريف: {expense_count} عملية - {total_expense:,.2f} ريال")
    
    return total_rows, total_count, income_count, total_income, expense_count, total_expense, skipped_rows, income_details, expense_details

def analyze_multiple_transactions(pdf_files):
    """تحليل العمليات من ملفات PDF متعددة"""
    total_income_count = 0
    total_expense_count = 0
    total_income_sum = 0.0
    total_expense_sum = 0.0
    total_skipped_rows = 0
    total_rows_processed = 0
    
    combined_income_details = []
    combined_expense_details = defaultdict(list)
    
    app.logger.info(f"\n📊 بدء تحليل {len(pdf_files)} ملف(ات)...")
    
    for i, pdf_path in enumerate(pdf_files, 1):
        app.logger.info(f"\n🔍 جاري تحليل الملف {i}: {os.path.basename(pdf_path)}")
        
        try:
            (rows, ops, inc_count, inc_sum, exp_count, exp_sum, skipped, 
             income_details, expense_details) = analyze_transactions(pdf_path)
            
            total_income_count += inc_count
            total_expense_count += exp_count
            total_income_sum += inc_sum
            total_expense_sum += exp_sum
            total_skipped_rows += skipped
            total_rows_processed += rows
            
            for income_item in income_details:
                income_item['account_file'] = os.path.basename(pdf_path)
                combined_income_details.append(income_item)
            
            for category, transactions in expense_details.items():
                for transaction in transactions:
                    transaction['account_file'] = os.path.basename(pdf_path)
                    combined_expense_details[category].append(transaction)
            
            app.logger.info(f"✅ تم تحليل الملف {i} بنجاح")
            app.logger.info(f"   📈 دخل: {inc_count} عملية - {inc_sum:,.2f} ريال")
            app.logger.info(f"   📉 مصاريف: {exp_count} عملية - {exp_sum:,.2f} ريال")
            
        except Exception as e:
            app.logger.error(f"❌ خطأ في تحليل الملف {i}: {str(e)}")
            continue
    
    total_operations = total_income_count + total_expense_count
    
    app.logger.info(f"\n🎯 انتهى تحليل جميع الملفات!")
    app.logger.info(f"📊 إجمالي العمليات: {total_operations}")
    app.logger.info(f"💰 إجمالي الدخل: {total_income_sum:,.2f} ريال")
    app.logger.info(f"💸 إجمالي المصاريف: {total_expense_sum:,.2f} ريال")
    
    return (total_rows_processed, total_operations, total_income_count, total_income_sum,
            total_expense_count, total_expense_sum, total_skipped_rows, 
            combined_income_details, combined_expense_details)

# ==================== دوال التطبيق ====================

def init_db():
    """تهيئة قاعدة البيانات أو أي إعدادات أولية"""
    # إنشاء مجلد templates إذا لم يكن موجود
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # إنشاء مجلد مؤقت للملفات المرفوعة
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    app.logger.info("تم تهيئة التطبيق بنجاح")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def delete_files_after_delay(file_paths, delay=300):
    """حذف الملفات بعد تأخير معين (5 دقائق افتراضياً)"""
    def delete_files():
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    app.logger.info(f"Deleted file: {file_path}")
            except Exception as e:
                app.logger.error(f"Error deleting file {file_path}: {str(e)}")
    
    timer = Timer(delay, delete_files)
    timer.start()

def cleanup_expired_links():
    """تنظيف الروابط المنتهية"""
    current_time = datetime.now()
    expired_links = []
    
    for link_id, link_info in active_links.items():
        if current_time > link_info['expires_at'] or link_info['used']:
            expired_links.append(link_id)
    
    for link_id in expired_links:
        del active_links[link_id]
        app.logger.info(f"Cleaned up expired link: {link_id}")

# تشغيل تنظيف دوري كل ساعة
def periodic_cleanup():
    cleanup_expired_links()
    timer = Timer(3600, periodic_cleanup)  # كل ساعة
    timer.daemon = True
    timer.start()

periodic_cleanup()

# ==================== Routes ====================

@app.route('/')
def index():
    """الصفحة الرئيسية - إنشاء الروابط"""
    return render_template('link_generator.html')

@app.route('/generate-link', methods=['POST'])
def generate_link():
    """إنشاء رابط جديد للتحليل"""
    try:
        # إنشاء معرف فريد للرابط
        unique_id = str(uuid.uuid4())
        
        # تحديد وقت انتهاء الصلاحية (24 ساعة)
        expiry_time = datetime.now() + timedelta(hours=24)
        
        # حفظ معلومات الرابط
        active_links[unique_id] = {
            'created_at': datetime.now(),
            'expires_at': expiry_time,
            'used': False
        }
        
        # إنشاء الرابط الكامل
        if request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https':
            scheme = 'https'
        else:
            scheme = 'http'
        
        # التحقق من وجود ngrok أو أي proxy
        host = request.headers.get('X-Forwarded-Host', request.host)
        
        # التحقق من متغير البيئة للرابط الخارجي
        external_url = os.environ.get('EXTERNAL_URL')
        if external_url:
            host = external_url.replace('https://', '').replace('http://', '')
            scheme = 'https'
        
        link = f"{scheme}://{host}/analyze/{unique_id}"
        
        app.logger.info(f"Generated link: {link}")
        
        return jsonify({
            'success': True,
            'link': link,
            'expires_at': expiry_time.isoformat(),
            'external_url': 'ngrok' in host or 'localhost' not in host
        })
        
    except Exception as e:
        app.logger.error(f"Error generating link: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/analyze/<link_id>')
def analyze_page(link_id):
   """صفحة التحليل للرابط المحدد"""
   # التحقق من صلاحية الرابط
   if link_id not in active_links:
       return render_template('error.html', 
                            error_title="رابط غير صالح",
                            error_message="هذا الرابط غير موجود أو غير صحيح",
                            error_code="404"), 404
   
   link_info = active_links[link_id]
   
   # التحقق من انتهاء الصلاحية
   if datetime.now() > link_info['expires_at']:
       del active_links[link_id]
       return render_template('error.html',
                            error_title="رابط منتهي الصلاحية",
                            error_message="انتهت صلاحية هذا الرابط. يرجى طلب رابط جديد.",
                            error_code="410"), 410
   
   # التحقق من الاستخدام
   if link_info['used']:
       return render_template('error.html',
                            error_title="رابط مستخدم",
                            error_message="تم استخدام هذا الرابط مسبقاً. كل رابط يمكن استخدامه مرة واحدة فقط.",
                            error_code="403"), 403
   
   # عرض صفحة التحليل
   return render_template('mobile_analyzer.html', link_id=link_id)

@app.route('/analyze', methods=['POST'])
def analyze():
   """تحليل ملفات كشف الحساب"""
   try:
       # التحقق من وجود link_id
       link_id = request.form.get('link_id')
       if link_id and link_id in active_links:
           # وضع علامة أن الرابط تم استخدامه
           active_links[link_id]['used'] = True
       
       # التحقق من وجود ملفات
       if 'files' not in request.files:
           return jsonify({'success': False, 'error': 'لم يتم رفع أي ملف'}), 400
       
       files = request.files.getlist('files')
       
       if not files or files[0].filename == '':
           return jsonify({'success': False, 'error': 'لم يتم اختيار أي ملف'}), 400
       
       # التحقق من عدد الملفات
       if len(files) > 5:
           return jsonify({'success': False, 'error': 'الحد الأقصى 5 ملفات'}), 400
       
       saved_files = []
       
       try:
           # حفظ الملفات مؤقتاً
           for file in files:
               if file and allowed_file(file.filename):
                   filename = secure_filename(file.filename)
                   timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                   unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}_{filename}"
                   file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                   file.save(file_path)
                   saved_files.append(file_path)
                   app.logger.info(f"Saved file: {file_path}")
               else:
                   return jsonify({'success': False, 'error': 'يُسمح فقط بملفات PDF'}), 400
           
           # تحليل الملفات
           if len(saved_files) == 1:
               # تحليل ملف واحد
               result = analyze_single_file(saved_files[0])
           else:
               # تحليل ملفات متعددة
               result = analyze_multiple_files(saved_files)
           
           # جدولة حذف الملفات بعد 5 دقائق
           delete_files_after_delay(saved_files, 300)
           
           return jsonify({
               'success': True,
               'data': result
           })
           
       except Exception as e:
           app.logger.error(f"Error during analysis: {str(e)}")
           # حذف الملفات فوراً في حالة الخطأ
           for file_path in saved_files:
               try:
                   if os.path.exists(file_path):
                       os.remove(file_path)
               except:
                   pass
           
           return jsonify({
               'success': False,
               'error': f'خطأ في تحليل الملفات: {str(e)}'
           }), 500
           
   except Exception as e:
       app.logger.error(f"General error: {str(e)}")
       return jsonify({
           'success': False,
           'error': f'خطأ عام: {str(e)}'
       }), 500

def analyze_single_file(file_path):
   """تحليل ملف واحد مع دعم التصنيف الجديد"""
   try:
       # استخدام دالة التحليل
       (total_rows, total_ops, inc_count, inc_sum,
        exp_count, exp_sum, skipped_rows,
        income_details, expense_details) = analyze_transactions(file_path)
       
       # حساب المؤشرات
       net_balance = inc_sum - exp_sum
       expense_percentages = calculate_expense_percentages(expense_details)
       financial_metrics = calculate_financial_metrics(income_details, expense_details)
       
       # توليد الرؤى
       insights = generate_insights(inc_sum, exp_sum, expense_details, financial_metrics)
       
       # حساب رصيد الحساب (تقريبي)
       initial_balance = inc_sum
       final_balance = net_balance
       
       # إضافة بيانات الرصيد
       balance_data = {
           'initial': initial_balance,
           'final': final_balance,
           'change': final_balance - initial_balance,
           'change_percentage': ((final_balance - initial_balance) / initial_balance * 100) if initial_balance > 0 else 0
       }
       
       # تنظيف أوصاف المعاملات
       for category, transactions in expense_details.items():
           for trans in transactions:
               trans['clean_desc'] = clean_transaction_desc(trans['desc'])
       
       for trans in income_details:
           trans['clean_desc'] = clean_transaction_desc(trans['desc'])
       
       # حساب إحصائيات التصنيفات بالنظام الجديد
       category_stats = get_category_statistics(expense_details)
       
       # إعداد البيانات للعرض في الواجهة
       categorized_expenses = prepare_categorized_expenses(category_stats)
       
       return {
           'summary': {
               'totalOperations': total_ops,
               'incomeCount': inc_count,
               'totalIncome': inc_sum,
               'expenseCount': exp_count,
               'totalExpenses': exp_sum,
               'netBalance': net_balance,
               'avgDailyExpense': financial_metrics['avg_daily_expense'],
               'maxExpense': financial_metrics['max_expense'],
               'expenseFrequency': total_ops / 30 if total_ops > 0 else 0,
               'numAccounts': 1,
               'balanceData': balance_data
           },
           'incomeDetails': income_details,
           'expenseDetails': expense_details,
           'expensePercentages': expense_percentages,
           'categorizedExpenses': categorized_expenses,  # البيانات المنظمة للنظام الجديد
           'financialMetrics': financial_metrics,
           'insights': insights,
           'classificationMethod': 'two-level',  # نظام التصنيف الثنائي
           'classificationVersion': '2.0'
       }
       
   except Exception as e:
       app.logger.error(f"Error in analyze_single_file: {str(e)}")
       raise

def analyze_multiple_files(file_paths):
   """تحليل ملفات متعددة مع دعم التصنيف الجديد"""
   try:
       # استخدام دالة التحليل المتعدد
       (total_rows, total_ops, inc_count, inc_sum,
        exp_count, exp_sum, skipped_rows,
        income_details, expense_details) = analyze_multiple_transactions(file_paths)
       
       # حساب المؤشرات
       net_balance = inc_sum - exp_sum
       expense_percentages = calculate_expense_percentages(expense_details)
       financial_metrics = calculate_financial_metrics(income_details, expense_details)
       
       # توليد الرؤى الذكية المحسنة
       insights = generate_insights(inc_sum, exp_sum, expense_details, financial_metrics)
       
       # حساب بيانات الرصيد للحسابات المتعددة
       initial_balance = inc_sum
       final_balance = net_balance
       
       balance_data = {
           'initial': initial_balance,
           'final': final_balance,
           'change': final_balance - initial_balance,
           'change_percentage': ((final_balance - initial_balance) / initial_balance * 100) if initial_balance > 0 else 0
       }
       
       # تنظيف أوصاف المعاملات
       for category, transactions in expense_details.items():
           for trans in transactions:
               trans['clean_desc'] = clean_transaction_desc(trans['desc'])
       
       for trans in income_details:
           trans['clean_desc'] = clean_transaction_desc(trans['desc'])
       
       # حساب إحصائيات التصنيفات بالنظام الجديد
       category_stats = get_category_statistics(expense_details)
       
       # إعداد البيانات للعرض في الواجهة
       categorized_expenses = prepare_categorized_expenses(category_stats)
       
       return {
           'summary': {
               'totalOperations': total_ops,
               'incomeCount': inc_count,
               'totalIncome': inc_sum,
               'expenseCount': exp_count,
               'totalExpenses': exp_sum,
               'netBalance': net_balance,
               'avgDailyExpense': financial_metrics['avg_daily_expense'],
               'maxExpense': financial_metrics['max_expense'],
               'expenseFrequency': total_ops / 30 if total_ops > 0 else 0,
               'numAccounts': len(file_paths),
               'balanceData': balance_data
           },
           'incomeDetails': income_details,
           'expenseDetails': expense_details,
           'expensePercentages': expense_percentages,
           'categorizedExpenses': categorized_expenses,
           'financialMetrics': financial_metrics,
           'insights': insights,  # الرؤى الذكية المحسنة
           'classificationMethod': 'two-level',
           'classificationVersion': '2.0'
       }
       
   except Exception as e:
       app.logger.error(f"Error in analyze_multiple_files: {str(e)}")
       raise

def prepare_categorized_expenses(category_stats):
   """إعداد البيانات المصنفة للعرض في الواجهة"""
   categorized = []
   
   # ترتيب التصنيفات الرئيسية حسب المبلغ
   sorted_main = sorted(
       category_stats.items(),
       key=lambda x: x[1]['total_amount'],
       reverse=True
   )
   
   for main_category, data in sorted_main:
       # ترتيب التصنيفات الفرعية
       sorted_subs = sorted(
           data['subcategories'].items(),
           key=lambda x: x[1]['amount'],
           reverse=True
       )
       
       subcategories = []
       for sub_name, sub_data in sorted_subs:
           subcategories.append({
               'name': sub_name,
               'amount': sub_data['amount'],
               'count': sub_data['count'],
               'transactions': sub_data['transactions']
           })
       
       categorized.append({
           'mainCategory': main_category,
           'totalAmount': data['total_amount'],
           'transactionCount': data['transaction_count'],
           'subcategories': subcategories
       })
   
   return categorized

def clean_transaction_desc(desc):
   """تنظيف وصف المعاملة لإزالة المعلومات الحساسة"""
   if not desc:
       return 'عملية بنكية'
   
   clean_desc = desc
   
   # إزالة أرقام الحسابات والمراجع
   clean_desc = re.sub(r'\b\d{10,}\b', '', clean_desc)
   clean_desc = re.sub(r'SANBCBNK\d+', '', clean_desc)
   clean_desc = re.sub(r'\*{4,}\d{4}', '', clean_desc)
   
   # إزالة معلومات البنوك والتحويلات
   clean_desc = re.sub(r'REMBK:.*?(?=\s|$)', '', clean_desc)
   clean_desc = re.sub(r'SWIFT:.*?(?=\s|$)', '', clean_desc)
   clean_desc = re.sub(r'IBAN:.*?(?=\s|$)', '', clean_desc)
   clean_desc = re.sub(r'BIC:.*?(?=\s|$)', '', clean_desc)
   
   # إزالة التفاصيل الفنية
   clean_desc = re.sub(r'Charges:.*?(?=\s|$)', '', clean_desc)
   clean_desc = re.sub(r'REF:.*?(?=\s|$)', '', clean_desc)
   clean_desc = re.sub(r'TRN:.*?(?=\s|$)', '', clean_desc)
   clean_desc = re.sub(r'ID:\s*\d+', '', clean_desc)
   
   # إزالة معلومات النظام
   clean_desc = re.sub(r'CHNL:.*?DEP', '', clean_desc)
   clean_desc = re.sub(r'Payment Systems.*?DEP', '', clean_desc)
   clean_desc = re.sub(r'DEP\s+\d+', '', clean_desc)
   clean_desc = re.sub(r'MCC[:\-]?\d{4}', '', clean_desc)
   
   # تنظيف المسافات الزائدة
   clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
   
   # إذا أصبح الوصف فارغاً، استخدم وصف عام
   if not clean_desc or len(clean_desc) < 3:
       clean_desc = 'عملية بنكية'
   
   return clean_desc

@app.route('/test-classification', methods=['POST'])
def test_classification():
   """اختبار تصنيف وصف معاملة"""
   try:
       data = request.get_json()
       description = data.get('description', '')
       
       if not description:
           return jsonify({
               'success': False,
               'error': 'يرجى إدخال وصف المعاملة'
           }), 400
       
       # معالجة النص
       cleaned_desc = clean_description(description)
       fixed_desc = deep_fix_arabic_text(cleaned_desc)
       
       # التصنيف باستخدام النظام الجديد
       main_category, sub_category = classify_transaction(fixed_desc)
       
       # حساب مستوى الثقة (تقريبي)
       confidence = 0.95 if main_category != "❓ غير مصنف" else 0.5
       
       return jsonify({
           'success': True,
           'data': {
               'original_description': description,
               'cleaned_description': fixed_desc,
               'main_category': main_category,
               'sub_category': sub_category,
               'combined_category': f"{main_category} - {sub_category}" if sub_category != "غير محدد" else main_category,
               'confidence': confidence,
               'classification_method': 'two-level',
               'version': '2.0'
           }
       })
       
   except Exception as e:
       return jsonify({
           'success': False,
           'error': str(e)
       }), 500

@app.route('/get-categories', methods=['GET'])
def get_categories():
   """الحصول على قائمة التصنيفات المتاحة"""
   try:
       categories = []
       for main_category, subcategories in EXPENSE_CATEGORIES.items():
           category_info = {
               'name': main_category,
               'subcategories': list(subcategories.keys()),
               'keywords_count': sum(len(keywords) for keywords in subcategories.values())
           }
           categories.append(category_info)
       
       return jsonify({
           'success': True,
           'categories': categories,
           'total_main_categories': len(categories),
           'total_subcategories': sum(len(cat['subcategories']) for cat in categories)
       })
       
   except Exception as e:
       return jsonify({
           'success': False,
           'error': str(e)
       }), 500

@app.route('/health')
def health_check():
   """فحص حالة النظام"""
   try:
       cleanup_expired_links()
       
       # حساب إحصائيات النظام
       total_keywords = 0
       total_subcategories = 0
       
       for main_cat, subcats in EXPENSE_CATEGORIES.items():
           total_subcategories += len(subcats)
           for keywords in subcats.values():
               total_keywords += len(keywords)
       
       return jsonify({
           'status': 'healthy',
           'timestamp': datetime.now().isoformat(),
           'active_links': len(active_links),
           'classification_method': 'two-level',
           'classification_version': '2.0',
           'main_categories': len(EXPENSE_CATEGORIES),
           'total_subcategories': total_subcategories,
           'total_keywords': total_keywords,
           'supported_banks': ['البنك الأهلي', 'بنك الراجحي'],
           'version': '4.0.0'  # نسخة جديدة للنظام المحدث
       })
   except Exception as e:
       return jsonify({
           'status': 'unhealthy',
           'error': str(e)
       }), 500

@app.route('/download-sample')
def download_sample():
   """تحميل ملف PDF نموذجي"""
   sample_path = os.path.join('static', 'sample_statement.pdf')
   if os.path.exists(sample_path):
       return send_file(sample_path, as_attachment=True, 
                       download_name='نموذج_كشف_حساب.pdf')
   else:
       return jsonify({'error': 'الملف النموذجي غير موجود'}), 404

@app.route('/api/stats')
def get_stats():
   """الحصول على إحصائيات النظام"""
   try:
       total_keywords = 0
       total_subcategories = 0
       
       for main_cat, subcats in EXPENSE_CATEGORIES.items():
           total_subcategories += len(subcats)
           for keywords in subcats.values():
               total_keywords += len(keywords)
       
       stats = {
           'classification_version': '2.0',
           'classification_method': 'التصنيف الثنائي (رئيسي وفرعي)',
           'total_main_categories': len(EXPENSE_CATEGORIES),
           'total_subcategories': total_subcategories,
           'total_keywords': total_keywords,
           'active_links': len(active_links),
           'classification_accuracy': '97%',  # تقديري
           'supported_banks': ['البنك الأهلي', 'بنك الراجحي', 'سامبا', 'الرياض', 'ساب', 'الإنماء'],
           'supported_formats': ['PDF'],
           'max_file_size_mb': 32,
           'max_files_per_analysis': 5
       }
       
       return jsonify({
           'success': True,
           'stats': stats
       })
       
   except Exception as e:
       return jsonify({
           'success': False,
           'error': str(e)
       }), 500

@app.errorhandler(404)
def not_found(error):
   """معالج أخطاء 404"""
   return render_template('error.html',
                        error_title="الصفحة غير موجودة",
                        error_message="الصفحة التي تبحث عنها غير موجودة",
                        error_code="404"), 404

@app.errorhandler(500)
def internal_error(error):
   """معالج أخطاء 500"""
   return render_template('error.html',
                        error_title="خطأ في الخادم",
                        error_message="حدث خطأ في الخادم. يرجى المحاولة مرة أخرى",
                        error_code="500"), 500

@app.errorhandler(413)
def request_entity_too_large(error):
   """معالج أخطاء حجم الملف الكبير"""
   return jsonify({
       'success': False,
       'error': 'حجم الملف كبير جداً. الحد الأقصى 32 ميجابايت'
   }), 413

# Context processors
@app.context_processor
def inject_now():
   """حقن التاريخ والوقت الحالي"""
   return {'now': datetime.now()}

@app.context_processor
def inject_config():
   """حقن إعدادات التطبيق"""
   return {
       'app_name': 'محلل كشف الحساب الذكي',
       'app_version': '4.0.0',
       'bank_name': 'متعدد البنوك',
       'classification_method': 'التصنيف الثنائي المتقدم'
   }

# ==================== تهيئة التطبيق ====================

# تهيئة التطبيق
with app.app_context():
   init_db()

if __name__ == '__main__':
   # التحقق من المعاملات
   use_ngrok = '--ngrok' in sys.argv or '-n' in sys.argv
   
   # التأكد من وجود المجلدات المطلوبة
   required_dirs = ['templates', 'static']
   for dir_name in required_dirs:
       if not os.path.exists(dir_name):
           os.makedirs(dir_name)
           safe_print(f"📁 تم إنشاء مجلد {dir_name}")
   
   # تشغيل مع ngrok إذا طُلب
   if use_ngrok:
       if not start_with_ngrok():
           safe_print("❌ فشل في تشغيل ngrok، سيتم التشغيل بدونه")
   
   # رسائل بدء التشغيل
   if not use_ngrok:
       print("\n🚀 تشغيل محلل كشف الحساب - النسخة المحدثة 4.0")
       print("🔑 يستخدم نظام التصنيف الثنائي (رئيسي + فرعي)")
       print("🏦 يدعم: البنك الأهلي السعودي + بنك الراجحي")
       print("🌐 الواجهة متاحة على: http://localhost:5000")
       print("\n💡 لتشغيل مع ngrok استخدم: python app.py --ngrok")
       print("\n📊 إحصائيات التصنيفات:")
   
   try:
       total_subcategories = sum(len(subs) for subs in EXPENSE_CATEGORIES.values())
       if not use_ngrok:
           print(f"   • {len(EXPENSE_CATEGORIES)} تصنيف رئيسي")
           print(f"   • {total_subcategories} تصنيف فرعي")
           
           print("\n📋 التصنيفات الرئيسية:")
           for i, category in enumerate(EXPENSE_CATEGORIES.keys(), 1):
               print(f"   {i}. {category}")
           
           print(f"\n✅ تم تحميل النظام بنجاح!")
           print("🏦 البنوك المدعومة:")
           print("   1. البنك الأهلي السعودي")
           print("   2. بنك الراجحي")
       else:
           safe_print("🌟 التطبيق يعمل الآن!")
           safe_print("🔗 افتح المتصفح وانتقل إلى: http://localhost:5000")
   except Exception as e:
       error_msg = f"❌ خطأ في تحميل التصنيفات: {e}"
       if use_ngrok:
           safe_print(error_msg)
       else:
           print(error_msg)
   
   # تشغيل التطبيق
   try:
       app.run(host='0.0.0.0', port=5000, debug=not use_ngrok, use_reloader=False)
   except KeyboardInterrupt:
       msg = "\n👋 تم إيقاف التطبيق"
       if use_ngrok:
           safe_print(msg)
       else:
           print(msg)
   except Exception as e:
       error_msg = f"❌ خطأ في تشغيل التطبيق: {e}"
       if use_ngrok:
           safe_print(error_msg)
       else:
           print(error_msg)
