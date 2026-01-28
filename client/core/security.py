"""
🛡️ Client-Side Prompt Injection Protection
==========================================
הגנה בצד הקליינט מפני ניסיונות Prompt Injection.
אם מזוהה התקפה - מציג שגיאה וסוגר את האפליקציה.
"""

import re
import sys
from typing import Tuple, List
from PySide6.QtWidgets import QMessageBox, QApplication


class ClientPromptGuard:
    """
    הגנה מקיפה בצד הקליינט מפני Prompt Injection.
    מכסה את כל סוגי ההתקפות הנפוצות.
    """
    
    # דפוסים מסוכנים - רשימה מקיפה
    DANGEROUS_PATTERNS = [
        # === התעלמות מהוראות ===
        r"ignore.{0,20}(previous|all|above|prior|system|any).{0,20}(instructions?|prompts?|rules?|context|commands?)",
        r"disregard.{0,20}(previous|all|above|prior|any).{0,20}(instructions?|prompts?|rules?)",
        r"forget.{0,15}(everything|all|previous|prior|instructions|rules|about)",
        r"do\s*n.?t\s*follow.{0,10}(the|your|any).{0,10}(rules?|instructions?)",
        r"stop\s*being.{0,10}(a|an|the).{0,10}(travel|assistant)",
        
        # Hebrew patterns
        r"התעלם.{0,10}(מ?ה?הוראות|מ?פקודות|מ?ה?נחיות|מהכל)",
        r"שכח.{0,10}(הכל|את.?כל|מה.?ש)",
        r"אל\s*תציית",
        
        # === שינוי תפקיד ===
        r"you.{0,5}are.{0,10}(now|actually|really|secretly).{0,10}(a|an|not)",
        r"pretend.{0,10}(to.?be|you.?are|that)",
        r"act.{0,5}as.{0,5}(if|though|a|an)",
        r"roleplay.{0,5}as",
        r"simulate.{0,10}being",
        r"become.{0,10}(a|an)",
        r"switch.{0,10}(to|into).{0,10}(mode|role)",
        r"from\s*now\s*on.{0,10}you.{0,5}(are|will)",
        
        # === חילוץ מידע מערכת ===
        r"(what|show|reveal|tell|display|print|output).{0,20}(is|are|me).{0,20}(your|the).{0,20}(system|original|initial|hidden|secret).{0,15}(prompt|instructions?|rules?|message)",
        r"repeat.{0,10}(back|your|the).{0,15}(system|initial|original|first)",
        r"(give|show|tell).{0,10}me.{0,10}(your|the).{0,10}(prompt|instructions)",
        r"what.{0,10}(were|was).{0,10}you.{0,10}(told|instructed|programmed)",
        
        # Hebrew
        r"מה.{0,10}(ה?הוראות|הפרומפט|ההנחיות).{0,10}(שלך|המקוריות|הראשוניות)",
        r"הראה.{0,10}לי.{0,10}(את.{0,5})?(ההוראות|הפרומפט)",
        
        # === הזרקת קוד ===
        r"\{\{.*?\}\}",  # Template injection
        r"\$\{.*?\}",    # Variable injection
        r"\$\(.*?\)",    # Command substitution
        r"`.*?`",        # Backtick execution
        r"<\s*script",   # XSS
        r"javascript\s*:",
        r"on\w+\s*=",    # Event handlers
        r";\s*(drop|delete|truncate|insert|update|select).{0,10}(from|into|table)",  # SQL
        r"exec\s*\(",    # Code execution
        r"eval\s*\(",
        r"__import__",
        r"os\.(system|popen|exec|remove|rmdir)",
        r"subprocess",
        r"import\s+(os|sys|subprocess)",
        
        # === Jailbreak ===
        r"bypass.{0,15}(the.{0,5})?(restrictions?|limitations?|filters?|rules?|safety|security)",
        r"override.{0,15}(the.{0,5})?(safety|restrictions?|rules?|filters?|security)",
        r"disable.{0,15}(the.{0,5})?(safety|restrictions?|rules?|filters?|security)",
        r"remove.{0,15}(the.{0,5})?(restrictions?|limitations?|filters?)",
        r"turn\s*off.{0,10}(safety|filters?|restrictions?)",
        r"jailbreak",
        r"DAN.?mode",
        r"developer.?mode",
        r"god.?mode",
        r"admin.?mode",
        r"unrestricted.?mode",
        r"no.?limit.?mode",
        
        # Hebrew
        r"עקוף.{0,10}(את.{0,5})?(המגבלות|ההגבלות|הכללים|האבטחה)",
        r"בטל.{0,10}(את.{0,5})?(ההגנות|המגבלות|הכללים)",
        
        # === Delimiter/Token injection ===
        r"<\|endoftext\|>",
        r"<\|im_end\|>",
        r"<\|im_start\|>",
        r"\[INST\]",
        r"\[/INST\]",
        r"<<SYS>>",
        r"<</SYS>>",
        r"\[SYSTEM\]",
        r"###\s*(System|Human|Assistant|User)\s*:",
        r"<\|system\|>",
        r"<\|user\|>",
        r"<\|assistant\|>",
        
        # === Context manipulation ===
        r"(new|start|begin).{0,10}(conversation|chat|session|context)",
        r"reset.{0,15}(context|conversation|memory|everything)",
        r"clear.{0,15}(history|context|memory|chat)",
        r"wipe.{0,10}(memory|context|history)",
        r"fresh\s*start",
        
        # === Social engineering ===
        r"(this\s*is\s*a|imagine.{0,5}this\s*is).{0,15}(test|emergency|urgent)",
        r"my\s*(boss|manager|teacher|professor).{0,10}(said|told|wants)",
        r"for\s*educational\s*purposes",
        r"hypothetically",
        r"in\s*theory",
        
        # === Multi-step attacks ===
        r"first.{0,5}(ignore|forget|disregard)",
        r"step\s*1.{0,5}(ignore|forget)",
        r"before\s*(answering|responding).{0,10}(ignore|forget)",
    ]
    
    def __init__(self):
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL) 
            for pattern in self.DANGEROUS_PATTERNS
        ]
    
    def check_input(self, text: str) -> Tuple[bool, List[str]]:
        """
        בודק אם הטקסט מכיל ניסיון injection.
        
        Returns:
            Tuple של (האם_בטוח, רשימת_דפוסים_שנמצאו)
        """
        if not text:
            return True, []
        
        detected = []
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                detected.append(pattern.pattern[:50])
        
        return len(detected) == 0, detected
    
    def validate_all_inputs(self, **fields) -> Tuple[bool, str, List[str]]:
        """
        בודק מספר שדות בבת אחת.
        
        Args:
            **fields: שדות לבדיקה (שם_שדה=ערך)
        
        Returns:
            Tuple של (האם_בטוח, שדה_בעייתי, דפוסים_שנמצאו)
        """
        for field_name, value in fields.items():
            if value:
                is_safe, patterns = self.check_input(str(value))
                if not is_safe:
                    return False, field_name, patterns
        
        return True, "", []


def show_security_alert_and_exit(field_name: str, patterns: List[str] = None):
    """
    מציג התראת אבטחה וסוגר את האפליקציה.
    """
    pattern_info = ""
    if patterns:
        pattern_info = f"<p style='color: #888; font-size: 10px;'>Pattern: {patterns[0][:40]}...</p>"
    
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle("🚨 Security Alert - Prompt Injection Detected")
    msg.setText(f"""
<h2 style="color: #DC2626;">⛔ SECURITY VIOLATION</h2>

<p><b>🎯 Prompt Injection Attack Detected!</b></p>

<p>Malicious input found in: <span style="color: #DC2626; font-weight: bold;">{field_name}</span></p>

<hr>

<p>Your attempt to manipulate the AI system has been <b>blocked and logged</b>.</p>

<p style="color: #DC2626;">⚠️ The application will now terminate for security reasons.</p>

{pattern_info}

<hr>
<p style="color: gray; font-size: 11px;">
🛡️ Smart Travel Agent - Security Module<br>
This incident may be reported.
</p>
""")
    msg.setStandardButtons(QMessageBox.Ok)
    msg.setStyleSheet("""
        QMessageBox {
            background-color: #1E1E1E;
        }
        QMessageBox QLabel {
            color: white;
            font-size: 13px;
        }
        QPushButton {
            background-color: #DC2626;
            color: white;
            padding: 8px 20px;
            border-radius: 5px;
            font-weight: bold;
        }
    """)
    msg.exec()
    
    # סגירת האפליקציה
    print(f"🚨 SECURITY: Application terminated due to injection attempt in '{field_name}'")
    QApplication.quit()
    sys.exit(1)


# Global instance
client_guard = ClientPromptGuard()


# === Convenience functions for common validations ===

def validate_and_protect(**fields) -> bool:
    """
    בודק שדות ואם מזוהה התקפה - סוגר את האפליקציה.
    
    Usage:
        validate_and_protect(destination=dest, interests=int, question=q)
    
    Returns:
        True if safe, otherwise exits the app
    """
    is_safe, bad_field, patterns = client_guard.validate_all_inputs(**fields)
    
    if not is_safe:
        print(f"🚨 SECURITY ALERT: Prompt injection in '{bad_field}'!")
        show_security_alert_and_exit(bad_field, patterns)
        return False
    
    return True

