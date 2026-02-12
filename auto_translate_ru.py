import polib
import re
from deep_translator import GoogleTranslator

po = polib.pofile('locale/ru/LC_MESSAGES/django.po')
translator = GoogleTranslator(source='auto', target='ru')

placeholder_pattern = re.compile(r"%\([^)]+\)[sd]")

for entry in po:

    # skip header
    if entry.msgid == "":
        entry.msgstr = entry.msgstr or ""
        continue

    # skip plural forms
    if entry.msgid_plural:
        continue

    # skip already translated
    if entry.msgstr:
        continue

    try:
        placeholders = placeholder_pattern.findall(entry.msgid)

        translated = translator.translate(entry.msgid)

        # restore placeholders
        for ph in placeholders:
            if ph not in translated:
                translated += f" {ph}"

        entry.msgstr = translated
        print("Translated:", entry.msgid)

    except Exception as e:
        print("Failed:", entry.msgid, e)
        entry.msgstr = ""

# 🔥 FINAL SAFETY PASS
for entry in po:
    if entry.msgstr is None:
        entry.msgstr = ""

po.save()
print("Done.")