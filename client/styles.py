STYLESHEET = """
    /* --- הגדרות בסיס --- */
    QMainWindow { background-color: #f0f2f5; }
    QWidget { font-family: 'Segoe UI', Arial, sans-serif; }
    
    /* --- טקסטים וכותרות --- */
    QLabel { color: #263238; }
    QLabel#Header { font-size: 26px; font-weight: 900; color: #1565c0; }
    QLabel#SectionTitle { font-size: 18px; font-weight: bold; color: #37474f; margin-bottom: 5px; }
    QLabel#InputLabel { font-size: 14px; font-weight: 600; color: #546e7a; margin-top: 5px; }

    /* --- שדות טקסט רגילים (LineEdit) --- */
    QLineEdit { 
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #cfd8dc;
        border-radius: 6px;
        padding: 8px 10px;
        font-size: 14px;
        min-height: 25px;
    }
    QLineEdit:focus { border: 2px solid #2196f3; }

    /* --- שדות מספרים (QSpinBox) - התיקון הגדול --- */
    QSpinBox {
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #cfd8dc;
        border-radius: 6px;
        padding: 8px 10px; /* רווח לטקסט */
        font-size: 14px;
        min-height: 25px;
    }
    QSpinBox:focus { border: 2px solid #2196f3; }

    /* כפתורי החצים (הריבועים עצמם) */
    QSpinBox::up-button, QSpinBox::down-button {
        subcontrol-origin: border;
        width: 25px; /* כפתורים רחבים שקל ללחוץ */
        background-color: #eceff1; /* אפור בהיר */
        border-left: 1px solid #cfd8dc;
    }

    QSpinBox::up-button {
        subcontrol-position: top right; /* ימין למעלה */
        border-top-right-radius: 6px; /* עיגול פינה */
        border-bottom: 1px solid #cfd8dc;
    }
    
    QSpinBox::down-button {
        subcontrol-position: bottom right; /* ימין למטה */
        border-bottom-right-radius: 6px; /* עיגול פינה */
    }

    QSpinBox::up-button:hover, QSpinBox::down-button:hover {
        background-color: #cfd8dc; /* הדגשה במעבר עכבר */
    }
    
    QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {
        background-color: #b0bec5; /* כהה יותר בלחיצה */
    }

    /* --- ציור החצים (המשולשים השחורים) --- */
    /* זה הטריק שמצייר חץ בלי תמונה */
    QSpinBox::up-arrow {
        image: none;
        width: 0; height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-bottom: 6px solid #37474f; /* צבע החץ (שחור/אפור כהה) */
        margin: 4px;
    }

    QSpinBox::down-arrow {
        image: none;
        width: 0; height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #37474f; /* צבע החץ */
        margin: 4px;
    }

    /* --- תיבת בחירה (ComboBox) --- */
    QComboBox {
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #cfd8dc;
        border-radius: 6px;
        padding: 8px 10px;
        font-size: 14px;
        min-height: 25px;
    }
    QComboBox:focus { border: 2px solid #2196f3; }
    
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 25px;
        border-left: 1px solid #cfd8dc;
        background-color: #eceff1;
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
    }
    
    /* חץ למטה ב-ComboBox */
    QComboBox::down-arrow {
        image: none;
        width: 0; height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #37474f;
        margin: 8px;
    }

    /* --- כפתורים --- */
    QPushButton#PrimaryBtn {
        background-color: #1565c0;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px;
        font-weight: bold;
        font-size: 16px;
    }
    QPushButton#PrimaryBtn:hover { background-color: #0d47a1; }
    QPushButton#PrimaryBtn:pressed { background-color: #002171; }
    QPushButton#PrimaryBtn:disabled { background-color: #b0bec5; color: #eceff1; }

    QPushButton#SecondaryBtn {
        background-color: white;
        color: #455a64;
        border: 1px solid #b0bec5;
        border-radius: 6px;
        padding: 6px 12px;
        font-weight: 600;
    }
    QPushButton#SecondaryBtn:hover { background-color: #f5f5f5; border: 1px solid #78909c; }

    /* --- טאבים (Login) --- */
    QPushButton.TabBtn {
        background-color: transparent;
        color: #90a4ae;
        border: none;
        border-bottom: 3px solid transparent;
        font-size: 16px;
        font-weight: bold;
        padding: 10px;
    }
    QPushButton.TabBtn[active="true"] {
        color: #1565c0;
        border-bottom: 3px solid #1565c0;
    }

    /* --- כרטיסים --- */
    QFrame#Card {
        background-color: white;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
    }
    
    /* --- גלילה --- */
    QScrollBar:vertical {
        border: none;
        background: #f1f1f1;
        width: 8px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #c1c1c1;
        min-height: 20px;
        border-radius: 4px;
    }
"""