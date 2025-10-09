import fitz  # PyMuPDF
import re
 
def extract_mcqs_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
 
    # Regex to capture MCQ format
    pattern = r"(?:Q)?(\d+)\.\s*(.*?)\n[aA]\)\s*(.*?)\n[bB]\)\s*(.*?)\n[cC]\)\s*(.*?)\n[dD]\)\s*(.*?)\nAnswer:\s*([a-dA-D])"
    matches = re.findall(pattern, text, re.DOTALL)
 
    mcqs = []
    for match in matches:
        _, question, a, b, c, d, ans = match
        mcqs.append({
            "question_no": _.strip(),
            "question": question.strip(),
            "option1": a.strip(),
            "option2": b.strip(),
            "option3": c.strip(),
            "option4": d.strip(),
            "correct_answer": ans.strip()
        })
    return mcqs