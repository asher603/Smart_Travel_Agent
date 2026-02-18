"""
Premium Travel Itinerary PDF Generator
Generates beautiful, professional travel documents
"""

import os
import base64
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as PDFImage, 
    Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT


# ============================================================================
#                           COLOR PALETTE
# ============================================================================
class Colors:
    """Consistent color scheme"""
    PRIMARY = colors.HexColor("#2563EB")
    PRIMARY_DARK = colors.HexColor("#1E40AF")
    PRIMARY_LIGHT = colors.HexColor("#DBEAFE")
    ACCENT = colors.HexColor("#8B5CF6")
    SUCCESS = colors.HexColor("#10B981")
    
    TEXT_DARK = colors.HexColor("#1E293B")
    TEXT_MEDIUM = colors.HexColor("#475569")
    TEXT_LIGHT = colors.HexColor("#94A3B8")
    
    BG_WHITE = colors.HexColor("#FFFFFF")
    BG_LIGHT = colors.HexColor("#F8FAFC")
    BG_CARD = colors.HexColor("#F1F5F9")
    
    BORDER = colors.HexColor("#E2E8F0")


# ============================================================================
#                           STYLES
# ============================================================================
def get_styles():
    """Create paragraph styles"""
    styles = getSampleStyleSheet()
    
    return {
        'MainTitle': ParagraphStyle(
            'MainTitle', parent=styles['Title'],
            fontSize=32, textColor=Colors.PRIMARY_DARK,
            alignment=TA_CENTER, fontName='Helvetica-Bold',
            spaceAfter=8, leading=38
        ),
        'Subtitle': ParagraphStyle(
            'Subtitle', parent=styles['Normal'],
            fontSize=14, textColor=Colors.TEXT_MEDIUM,
            alignment=TA_CENTER, spaceAfter=5
        ),
        'SectionHeader': ParagraphStyle(
            'SectionHeader', parent=styles['Heading2'],
            fontSize=16, textColor=Colors.PRIMARY_DARK,
            fontName='Helvetica-Bold', spaceBefore=20, spaceAfter=12
        ),
        'BodyText': ParagraphStyle(
            'BodyText', parent=styles['Normal'],
            fontSize=11, textColor=Colors.TEXT_MEDIUM,
            leading=16, spaceAfter=8
        ),
        'ActivityText': ParagraphStyle(
            'ActivityText', parent=styles['Normal'],
            fontSize=10, textColor=Colors.TEXT_DARK,
            leftIndent=12, spaceBefore=4, spaceAfter=4, leading=14
        ),
        'SmallText': ParagraphStyle(
            'SmallText', parent=styles['Normal'],
            fontSize=9, textColor=Colors.TEXT_LIGHT,
            alignment=TA_CENTER
        ),
    }


# ============================================================================
#                           COMPONENTS
# ============================================================================
def create_header(destination, start_date, end_date, duration):
    """Create header with title and dates"""
    elements = []
    styles = get_styles()
    
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"✈️ Your Trip to <b>{destination}</b>", styles['MainTitle']))
    
    if start_date and end_date:
        elements.append(Paragraph(
            f"📅 {start_date}  →  {end_date}  •  {duration} Days",
            styles['Subtitle']
        ))
    
    elements.append(Spacer(1, 5))
    elements.append(HRFlowable(width="80%", thickness=2, color=Colors.PRIMARY, 
                               spaceAfter=15, hAlign='CENTER'))
    
    return elements


def create_info_card(icon, label, value):
    """Create a single info card"""
    cell = Table([
        [Paragraph(f"<font size='20'>{icon}</font>", 
                   ParagraphStyle('Icon', alignment=TA_CENTER))],
        [Paragraph(f"<font size='9' color='#64748B'><b>{label}</b></font>", 
                   ParagraphStyle('Label', alignment=TA_CENTER))],
        [Paragraph(f"<font size='12' color='#1E293B'><b>{value}</b></font>", 
                   ParagraphStyle('Value', alignment=TA_CENTER))]
    ], colWidths=[5*cm])
    
    cell.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), Colors.BG_CARD),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 1, Colors.BORDER),
    ]))
    return cell


def create_info_section(trip_data, weather_info):
    """Create info cards section"""
    elements = []
    
    origin = trip_data.get("origin", "N/A")
    budget = trip_data.get("budget", "N/A")
    currency = trip_data.get("currency", "USD")
    vibe = trip_data.get("analyzed_vibe", "Adventure")
    interests = trip_data.get("interest", trip_data.get("interests", ""))
    
    # Info cards row
    info_table = Table([[
        create_info_card("📍", "FROM", str(origin)),
        create_info_card("💰", "BUDGET", f"{budget} {currency}"),
        create_info_card("✨", "VIBE", str(vibe)),
    ]], colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 12))
    
    # Weather card
    if weather_info:
        weather = Table([[f"🌤️ Weather Forecast: {weather_info}"]], colWidths=[16.5*cm])
        weather.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEF3C7")),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#92400E")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#FDE68A")),
        ]))
        elements.append(weather)
        elements.append(Spacer(1, 12))
    
    # Interests card
    if interests and interests != "N/A":
        int_table = Table([[f"🎯 Interests: {interests}"]], colWidths=[16.5*cm])
        int_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), Colors.PRIMARY_LIGHT),
            ('TEXTCOLOR', (0, 0), (-1, -1), Colors.PRIMARY_DARK),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 1, Colors.BORDER),
        ]))
        elements.append(int_table)
    
    return elements


def create_summary(summary):
    """Create summary section"""
    if not summary:
        return []
    
    styles = get_styles()
    elements = []
    
    elements.append(Paragraph("📝 Trip Overview", styles['SectionHeader']))
    
    box = Table([[Paragraph(summary, styles['BodyText'])]], colWidths=[16.5*cm])
    box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), Colors.BG_LIGHT),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 1, Colors.BORDER),
    ]))
    elements.append(box)
    
    return elements


def create_budget_table(budget_breakdown, currency):
    """Create budget breakdown table"""
    if not budget_breakdown or not isinstance(budget_breakdown, dict):
        return []
    
    styles = get_styles()
    elements = []
    
    elements.append(Paragraph("💳 Budget Breakdown", styles['SectionHeader']))
    
    # Icon mapping
    icons = {
        'flight': '✈️', 'accommodation': '🏨', 'hotel': '🏨',
        'food': '🍽️', 'dining': '🍽️', 'activities': '🎯',
        'transport': '🚕', 'shopping': '🛍️', 'other': '📦'
    }
    
    rows = [["Category", "Estimated Cost"]]
    total = 0
    
    for category, amount in budget_breakdown.items():
        try:
            amt = float(str(amount).replace(',', '').replace('$', '').replace('€', ''))
            total += amt
            
            icon = '💵'
            for key, emoji in icons.items():
                if key in category.lower():
                    icon = emoji
                    break
            
            rows.append([f"{icon}  {category.title()}", f"{amt:,.0f} {currency}"])
        except (ValueError, TypeError):
            rows.append([f"💵  {category.title()}", str(amount)])
    
    rows.append(["🧾  TOTAL", f"{total:,.0f} {currency}"])
    
    table = Table(rows, colWidths=[10*cm, 6.5*cm])
    table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), Colors.PRIMARY_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        # Body
        ('FONTSIZE', (0, 1), (-1, -2), 10),
        ('TEXTCOLOR', (0, 1), (-1, -2), Colors.TEXT_DARK),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [Colors.BG_WHITE, Colors.BG_LIGHT]),
        # Total
        ('BACKGROUND', (0, -1), (-1, -1), Colors.PRIMARY_LIGHT),
        ('TEXTCOLOR', (0, -1), (-1, -1), Colors.PRIMARY_DARK),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 1.5, Colors.BORDER),
        ('LINEBELOW', (0, 0), (-1, 0), 2, Colors.PRIMARY),
        ('LINEABOVE', (0, -1), (-1, -1), 1, Colors.BORDER),
    ]))
    
    elements.append(table)
    return elements


def create_day_card(day_data, color):
    """Create a styled day card"""
    styles = get_styles()
    
    day_num = day_data.get("day", "?")
    title = day_data.get("title", "Day Plan")
    activities = day_data.get("activities", [])
    
    # Activities
    activity_rows = []
    for i, activity in enumerate(activities if isinstance(activities, list) else []):
        bullet = "▸" if i % 2 == 0 else "◦"
        activity_rows.append([Paragraph(
            f"<font color='#2563EB'>{bullet}</font>  {activity}",
            styles['ActivityText']
        )])
    
    # Header
    header = Table([[
        Paragraph(f"<font size='18' color='white'><b>Day {day_num}</b></font>",
                  ParagraphStyle('DN', alignment=TA_CENTER)),
        Paragraph(f"<font size='13' color='#1E40AF'><b>{title}</b></font>",
                  ParagraphStyle('DT', alignment=TA_LEFT, leftIndent=10))
    ]], colWidths=[2.2*cm, 14.3*cm])
    
    header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), color),
        ('BACKGROUND', (1, 0), (1, 0), Colors.PRIMARY_LIGHT),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (1, 0), (1, 0), 15),
    ]))
    
    # Activities table
    if activity_rows:
        act_table = Table(activity_rows, colWidths=[16.5*cm])
        act_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), Colors.BG_WHITE),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ]))
    else:
        act_table = Spacer(1, 5)
    
    # Combine
    card = Table([[header], [act_table]], colWidths=[16.5*cm])
    card.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, Colors.BORDER),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
    ]))
    
    return KeepTogether([card, Spacer(1, 12)])


def create_itinerary(itinerary):
    """Create full itinerary section"""
    if not itinerary:
        return []
    
    styles = get_styles()
    elements = []
    
    elements.append(Paragraph("📅 Your Itinerary", styles['SectionHeader']))
    elements.append(Spacer(1, 8))
    
    # Color rotation
    day_colors = [
        Colors.PRIMARY, Colors.ACCENT, Colors.SUCCESS,
        colors.HexColor("#EC4899"), colors.HexColor("#F97316"),
        colors.HexColor("#06B6D4"),
    ]
    
    for i, day in enumerate(itinerary):
        color = day_colors[i % len(day_colors)]
        elements.append(create_day_card(day, color))
    
    return elements


def create_hotels_section(hotels, currency="USD"):
    """Create recommended hotels section"""
    if not hotels or not isinstance(hotels, list):
        return []

    styles = get_styles()
    elements = []

    elements.append(Paragraph("🏨 Recommended Hotels", styles['SectionHeader']))
    elements.append(Spacer(1, 6))

    tier_colors = [Colors.SUCCESS, Colors.PRIMARY, colors.HexColor("#F59E0B")]
    tier_labels = ["Budget Pick", "Best Value", "Premium"]

    for idx, hotel in enumerate(hotels[:3]):
        accent = tier_colors[idx] if idx < len(tier_colors) else Colors.PRIMARY
        tier = tier_labels[idx] if idx < len(tier_labels) else "Hotel"

        name = hotel.get("name", "Hotel")
        stars = hotel.get("stars", 0)
        star_str = "★" * int(stars) + "☆" * (5 - int(stars))
        neighborhood = hotel.get("neighborhood", "")
        price = hotel.get("price_per_night", 0)
        highlights = hotel.get("highlights", [])
        why = hotel.get("why", "")

        # Build hotel info rows
        info_parts = []
        info_parts.append(f"<font size='7' color='#64748B'><b>{tier}</b></font>")
        info_parts.append(f"<font size='13' color='#1E293B'><b>{name}</b></font>")
        info_parts.append(f"<font size='11' color='{accent.hexval()}'>{star_str}</font>")

        if neighborhood:
            info_parts.append(f"<font size='10' color='#64748B'>📍 {neighborhood}</font>")

        info_parts.append(
            f"<font size='11' color='{accent.hexval()}'><b>💰 {price} {currency} / night</b></font>"
        )

        if highlights:
            chips = "  •  ".join(h for h in highlights[:4])
            info_parts.append(f"<font size='9' color='#475569'>{chips}</font>")

        if why:
            info_parts.append(f"<font size='9' color='#64748B'><i>💡 {why}</i></font>")

        cell_content = "<br/>".join(info_parts)

        row_table = Table(
            [[Paragraph(cell_content, ParagraphStyle('HotelCell', leading=16))]],
            colWidths=[16.5 * cm],
        )
        row_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), Colors.BG_LIGHT),
            ('BOX', (0, 0), (-1, -1), 1, accent),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))

        elements.append(KeepTogether([row_table, Spacer(1, 10)]))

    return elements


def create_footer():
    """Create document footer"""
    styles = get_styles()
    elements = []
    
    elements.append(Spacer(1, 25))
    elements.append(HRFlowable(width="100%", thickness=1, color=Colors.BORDER, spaceAfter=10))
    
    now = datetime.now().strftime("%B %d, %Y at %H:%M")
    elements.append(Paragraph(f"Generated by <b>Smart Travel Agent</b>  •  {now}", styles['SmallText']))
    elements.append(Spacer(1, 3))
    elements.append(Paragraph("🤖 Powered by AI  •  Have a wonderful trip! ✨", styles['SmallText']))
    
    return elements


def create_packing_list_section(packing_list):
    """Create packing list section with categories and items"""
    if not packing_list or not isinstance(packing_list, list):
        return []

    styles = get_styles()
    elements = []

    elements.append(Paragraph("🎒 Packing List", styles['SectionHeader']))
    elements.append(Spacer(1, 6))

    cat_icons = {
        "clothing": "👕", "toiletries": "🧴", "electronics": "📱",
        "documents": "📄", "accessories": "🎒", "health": "💊",
        "gear": "⛺", "footwear": "👟", "food": "🍫",
        "entertainment": "🎧", "misc": "📦",
    }

    cat_colors_cycle = [
        Colors.PRIMARY, Colors.ACCENT, Colors.SUCCESS,
        colors.HexColor("#F59E0B"), colors.HexColor("#EC4899"),
        colors.HexColor("#06B6D4"), colors.HexColor("#EF4444"),
    ]

    for idx, category in enumerate(packing_list):
        cat_name = category.get("category", "Items")
        items = category.get("items", [])
        icon = cat_icons.get(cat_name.lower(), "📋")
        accent = cat_colors_cycle[idx % len(cat_colors_cycle)]

        # Build item rows with checkbox squares
        item_rows = []
        for item in items:
            item_rows.append([Paragraph(
                f"<font color='{accent.hexval()}'>☐</font>  {item}",
                styles['ActivityText']
            )])

        # Category header
        header = Table([[
            Paragraph(
                f"<font size='12' color='white'><b>{icon}</b></font>",
                ParagraphStyle('CatIcon', alignment=TA_CENTER)
            ),
            Paragraph(
                f"<font size='11' color='#1E40AF'><b>{cat_name}</b></font>",
                ParagraphStyle('CatName', alignment=TA_LEFT, leftIndent=10)
            ),
            Paragraph(
                f"<font size='9' color='#64748B'>{len(items)} items</font>",
                ParagraphStyle('CatCount', alignment=TA_LEFT)
            ),
        ]], colWidths=[1.5*cm, 10*cm, 5*cm])

        header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), accent),
            ('BACKGROUND', (1, 0), (-1, 0), Colors.PRIMARY_LIGHT),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (1, 0), (1, 0), 12),
        ]))

        if item_rows:
            items_table = Table(item_rows, colWidths=[16.5*cm])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), Colors.BG_WHITE),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ]))
        else:
            items_table = Spacer(1, 5)

        card = Table([[header], [items_table]], colWidths=[16.5*cm])
        card.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, Colors.BORDER),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 8),
        ]))

        elements.append(KeepTogether([card, Spacer(1, 10)]))

    return elements


# ============================================================================
#                           MAIN FUNCTION
# ============================================================================
def generate_trip_pdf(trip_data, filename, image_base64=None, weather_info=None):
    """
    Generate a premium travel itinerary PDF.
    """
    doc = SimpleDocTemplate(
        filename, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    
    story = []
    temp_image_path = None
    
    # Extract data
    destination = trip_data.get("destination", "Your Destination")
    start_date = trip_data.get("start_date", "")
    end_date = trip_data.get("end_date", "")
    duration = trip_data.get("duration", "")
    summary = trip_data.get("summary", "")
    budget_breakdown = trip_data.get("budget_breakdown", {})
    itinerary = trip_data.get("itinerary", [])
    hotels = trip_data.get("hotels", [])
    packing_list = trip_data.get("packing_list", [])
    currency = trip_data.get("currency", "USD")
    
    # ==================== BUILD PDF ====================
    
    # Header
    story.extend(create_header(destination, start_date, end_date, duration))
    
    # Image
    if image_base64:
        try:
            image_data = base64.b64decode(image_base64)
            temp_image_path = tempfile.mktemp(suffix='.png')
            with open(temp_image_path, 'wb') as f:
                f.write(image_data)
            
            img = PDFImage(temp_image_path, width=15*cm, height=9*cm)
            img.hAlign = 'CENTER'
            
            img_box = Table([[img]], colWidths=[16.5*cm])
            img_box.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('BOX', (0, 0), (-1, -1), 2, Colors.BORDER),
                ('BACKGROUND', (0, 0), (-1, -1), Colors.BG_LIGHT),
            ]))
            
            story.append(img_box)
            story.append(Spacer(1, 15))
        except Exception as e:
            print(f"⚠️ Could not add image: {e}")
    
    # Info section
    story.extend(create_info_section(trip_data, weather_info))
    story.append(Spacer(1, 10))
    
    # Summary
    story.extend(create_summary(summary))
    story.append(Spacer(1, 10))
    
    # Budget
    story.extend(create_budget_table(budget_breakdown, currency))
    story.append(Spacer(1, 15))
    
    # Itinerary
    story.extend(create_itinerary(itinerary))
    
    # Hotels
    story.extend(create_hotels_section(hotels, currency))
    
    # Packing List
    story.extend(create_packing_list_section(packing_list))
    
    # Footer
    story.extend(create_footer())
    
    # Build
    try:
        doc.build(story)
        print(f"✅ PDF generated: {filename}")
    except Exception as e:
        print(f"❌ PDF error: {e}")
        raise
    finally:
        if temp_image_path and os.path.exists(temp_image_path):
            try:
                os.remove(temp_image_path)
            except:
                pass
