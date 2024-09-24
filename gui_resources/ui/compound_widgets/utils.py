

def fix_line_edit_width(line_edit, length=10):
    # Fix the width of line edits so that they don't expand with the window, but also fit an adequate amount of text
    fm = line_edit.fontMetrics()
    m = line_edit.textMargins()
    c = line_edit.contentsMargins()
    w = length * fm.width('x') + m.left() + m.right() + c.left() + c.right()

    # From SO: "The 8 comes from 2*d->horizontalMargin and the frame. The mysterious horizontalMargin and
    #           verticalMargin values are static constants found in qlineedit_p.cpp"
    line_edit.setMaximumWidth(w + 8)