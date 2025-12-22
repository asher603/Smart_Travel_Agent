STYLESHEET = """
    /* --- הגדרות בסיס (Fusion) --- */
    QMainWindow { background-color: #eceff1; }
    QWidget { font-family: 'Segoe UI', Arial, sans-serif; }
    
    /* --- טקסטים --- */
    QLabel { color: #263238; }
    QLabel#LoginHeader { font-size: 36px; font-weight: 900; color: #0d47a1; margin-bottom: 10px; }
    QLabel#LoginSub { font-size: 16px; color: #546e7a; }
    QLabel#Header { font-size: 24px; font-weight: bold; color: #37474f; }
    QLabel#CardTitle { font-size: 18px; font-weight: bold; color: #1565c0; }

    /* --- שדות קלט --- */
    QLineEdit { 
        background-color: white;
        color: black;
        border: 2px solid #cfd8dc;
        border-radius: 8px;
        padding: 10px;
        font-size: 16px;
    }
    QLineEdit:focus { border: 2px solid #2196f3; }

    /* --- כפתור ראשי (חייב border: none לתיקון הצבע) --- */
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

    /* --- כפתור הרשמה --- */
    QPushButton#RegisterBtn {
        background-color: white;
        color: #1565c0;
        border: 2px solid #1565c0;
        border-radius: 8px;
        padding: 12px;
        font-weight: bold;
        font-size: 16px;
    }
    QPushButton#RegisterBtn:hover { background-color: #e3f2fd; }

    /* --- כרטיס --- */
    QFrame#Card {
        background-color: white;
        border-radius: 16px;
        border: 1px solid #cfd8dc;
    }
    
    /* --- כפתור משני --- */
    QPushButton#SecondaryBtn {
        background-color: white;
        color: #455a64;
        border: 1px solid #b0bec5;
        border-radius: 6px;
        padding: 8px 16px;
    }
    
    QSpinBox, QComboBox {
        background-color: white;
        color: black;
        padding: 8px;
        border: 1px solid #cfd8dc;
        border-radius: 6px;
    }
"""