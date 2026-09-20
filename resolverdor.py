import io
import time
import cv2
import numpy as np
import pyautogui
import requests

pyautogui.FAILSAFE = True

API_KEY = "SUA_CHAVE_DE_TEXTO_AQUI" 

def calibrar_posicoes():
    #aqui tu deixa o mouse parado no canto superior esquerdo
    time.sleep(3)
    x1, y1 = pyautogui.position()
    #aqui no inferior direito
    time.sleep(3)
    x2, y2 = pyautogui.position()
    #no meio do botão de enviar
    time.sleep(3)
    bx, by = pyautogui.position()
    return (x1, y1, x2 - x1, y2 - y1), (bx, by)

def enviar_para_vision_ai(image_bytes):
    import base64
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://googleapis.com/{API_KEY}"
    payload = {
        "requests": [{
            "image": {"content": base64_image},
            "features": [{"type": "OBJECT_LOCALIZATION"}]
        }]
    }
    response = requests.post(url, json=payload)
    resultado = response.json()
    if 'responses' in resultado and 'localizedObjectAnnotations' in resultado['responses']:
        return resultado['responses']['localizedObjectAnnotations']
    return []
def capturar_e_resolver(regiao_captcha, botao_verificar, objeto_alvo, colunas=3, linhas=3):
    printscreen = pyautogui.screenshot(region=regiao_captcha)
    img_np = np.array(printscreen)
    img_cv2 = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    h_img, w_img, _ = img_cv2.shape

    _, encoded_image = cv2.imencode('.jpg', img_cv2)
    content = encoded_image.tobytes()

    objetos = enviar_para_vision_ai(content)
    mascara_objeto = np.zeros((h_img, w_img), dtype=np.uint8)

    for obj in objetos:
        if obj['name'].lower() == objeto_alvo.lower():
            vertices = [(int(v.get('x', 0) * w_img), int(v.get('y', 0) * h_img)) for v in obj['boundingPoly']['normalizedVertices']]
            pts = np.array(vertices, np.int32).reshape((-1, 1, 2))
            cv2.fillPoly(mascara_objeto, [pts], 255)

    origem_x, origem_y, _, _ = regiao_captcha
    largura_quadrado = w_img // colunas
    altura_quadrado = h_img // linhas

    for l in range(linhas):
        for c in range(colunas):
            x1_q, y1_q = c * largura_quadrado, l * altura_quadrado
            x2_q, y2_q = min((c + 1) * largura_quadrado, w_img), min((l + 1) * altura_quadrado, h_img)

            regiao_mascara = mascara_objeto[y1_q:y2_q, x1_q:x2_q]
            pixels_objeto = cv2.countNonZero(regiao_mascara)
            total_pixels = (x2_q - x1_q) * (y2_q - y1_q)
            porcentagem = (pixels_objeto / total_pixels) * 100

            centro_tela_x = origem_x + x1_q + (largura_quadrado // 2)
            centro_tela_y = origem_y + y1_q + (altura_quadrado // 2)

            pyautogui.moveTo(centro_tela_x, centro_tela_y, duration=0.2)

            if porcentagem >= 30.0:
                pyautogui.click()
                time.sleep(0.2)

    time.sleep(0.5)
    pyautogui.moveTo(botao_verificar, duration=0.3)
    pyautogui.click()

if __name__ == "__main__":
    regiao, botao = calibrar_posicoes()
    time.sleep(2)
    capturar_e_resolver(regiao, botao, "Traffic light", 3, 3)
    
