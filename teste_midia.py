from PIL import Image
import imagehash

def comparar_imagens(img1_path, img2_path, limiar=5):
    # Carregar imagens
    img1 = Image.open(img1_path)
    img2 = Image.open(img2_path)

    # Gerar hash perceptual
    hash1 = imagehash.phash(img1)
    hash2 = imagehash.phash(img2)

    # Calcular diferença
    diferenca = hash1 - hash2

    if diferenca <= limiar:
        return f"As imagens são semelhantes (diferença {diferenca})."
    else:
        return f"As imagens são diferentes (diferença {diferenca})."


def main() -> None:


    app = comparar_imagens("E:\work\ProjetoWhatsApp\downloads\whatsapp_1786478900134_1cadc626.jpg","E:\SERGIO\particular\FOTOS\Fotos-whatsApp-ISADORA\whatsapp_1786460598506_aeeba936.jpg")

    print(app)

if __name__ == "__main__":

    main()
