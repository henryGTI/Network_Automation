from PIL import Image, ImageDraw

# 16x16 크기의 이미지 생성
img = Image.new('RGB', (16, 16), color='white')
draw = ImageDraw.Draw(img)

# 간단한 네트워크 아이콘 그리기
draw.rectangle([2, 2, 14, 14], outline='blue')
draw.line([4, 8, 12, 8], fill='blue', width=1)
draw.line([8, 4, 8, 12], fill='blue', width=1)

# ICO 파일로 저장
img.save('favicon.ico', format='ICO') 