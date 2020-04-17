import arabic_reshaper
import serial
from . import api
from ..helpers import post_process_order,get_existing_order_from_request

from flask import request
from escpos import printer
from bidi.algorithm import get_display
from wand.image import Image as wImage
from wand.drawing import Drawing as wDrawing
from wand.color import Color as wColor
from flask.json import loads
from PIL import Image
import PIL
@api.route('/print_receipt', methods=['POST'])
def print_receipt():

    receipt_from_tailpos = loads(request.get_data(as_text=True))
    for_printing = receipt_from_tailpos['data']
    type_of_printing = receipt_from_tailpos['type']
    print(for_printing)

    port_serial = "/dev/rfcomm0"

    bluetoothSerial = serial.Serial(port_serial, baudrate=115200, timeout=1)
    #fontPath = "/home/jiloysss/Documents/spiceco/aljazeera-font/FontAljazeeraColor-lzzD.ttf"
    fontPath = "/home/pi/FontAljazeeraColor-lzzD.ttf"
    tmpImage = 'receipt.png'
    #printWidth = 375
    printWidth = 570

    height = 600
    draw = wDrawing()
    draw.font = fontPath

    #COMPANY ==============
    draw.font_size = 34
    y_value = 30
    draw.text(x=180,y=y_value,body=for_printing['company'])

    y_value = y_value + 35

    #DATE ==================
    split_date = for_printing['date'].split()
    draw.font_size = 26
    draw.text(x=5,y=y_value,body=split_date[0])
    draw.text(x=260,y=y_value,body=split_date[1])

    y_value = y_value + 35

    #ORDER TYPE ==============
    draw.font_size = 26
    draw.text(x=5,y=y_value,body="Order Type: " +  for_printing['ordertype'])

    #HEADER ==========

    if for_printing['header']:
        header_value = y_value + 15
        for x in for_printing['header'].split("\n"):
            y_value = y_value + 35
            header_value = header_value + 25
            draw.text_alignment = "center"
            draw.text(x=300,y=header_value,body=x)

    draw.text_alignment = "undefined"

    draw.text(x=5,y=y_value + 35 ,body="=====================================")

    #ITEM PURCHASES
    y_value = y_value + 30
    for idx,i in enumerate(for_printing['lines']):
        if idx != 0:
            height += 35
        draw.gravity = "north_east"
        draw.text(x=5,y=y_value + 10,body=format(float(i['qty'] * i['price']), '.2f'))
        draw.gravity = "forget"

        if len(i['item_name']) > 25:
            quotient = len(i['item_name']) / 25
            for xxx in range(0,int(quotient)):
                if idx != 0:
                    height += 35
                y_value = y_value + 35
                draw.text(x=5,y=y_value,body=i['item_name'][xxx * 25: (xxx+1) * 25])

            y_value = y_value + 35
            draw.text(x=5,y=y_value,body=i['item_name'][(int(quotient)*25): len(i['item_name'])])
            if i['translation_text']:
                y_value = y_value + 35
                textReshaped = arabic_reshaper.reshape(i['translation_text'])
                textDisplay = get_display(textReshaped)
                translation_text = "(" + textDisplay + ")"

                draw.text(x=5,y=y_value,body=translation_text)

        else:
            y_value = y_value + 35
            draw.text(x=5,y=y_value,body=i['item_name'] )
            if i['translation_text']:
                y_value = y_value + 35
                textReshaped = arabic_reshaper.reshape(i['translation_text'])
                textDisplay = get_display(textReshaped)
                translation_text = "(" +textDisplay + ")"
                draw.text(x=5,y=y_value,body= translation_text)


    draw.text(x=5,y=y_value+35,body="=====================================")

    y_value = y_value + 35

    #SUBTOTAL
    textReshaped = arabic_reshaper.reshape("المبلغ الاجمالي")
    textDisplaySubtotal = get_display(textReshaped)
    draw.text(x=5,y=y_value + 35,body="Subtotal("+ textDisplaySubtotal+ ")")
    draw.gravity = "north_east"
    draw.text(x=5,y=y_value + 5,body=for_printing['subtotal'])
    draw.gravity = "forget"

    y_value = y_value + 35

    #DISCOUNT
    textReshaped = arabic_reshaper.reshape("الخصم")
    textDisplayDiscount = get_display(textReshaped)
    draw.text(x=5,y=y_value + 35,body="Discount(" + textDisplayDiscount+ ")")
    draw.gravity = "north_east"
    draw.text(x=5,y=y_value + 5,body=for_printing['discount'])
    draw.gravity = "forget"

    #TAXES VALUES
    if len(for_printing['taxesvalues']) > 0:
        y_value = y_value + 35
        for idx,iii in enumerate(for_printing['taxesvalues']):
            if idx != 0:
                height += 35
            y_value = y_value + 35

            draw.text(x=5,y=y_value,body=iii['name'])
            draw.gravity = "north_east"
            draw.text(x=5,y=y_value - 25,body=str(format(round(float(iii['totalAmount']),2), '.2f')))
            draw.gravity = "forget"

    if len(for_printing['taxesvalues']) == 0:
        y_value = y_value + 35

    #MODE OF PAYMENT
    if type_of_printing != "Bill":
        for idx, ii in enumerate(loads(for_printing['mop'])):
            if idx != 0:
                height += 35
            y_value = y_value + 35
            type = ii['type']

            if ii['translation_text']:
                textReshaped = arabic_reshaper.reshape(ii['translation_text'])
                textDisplay = get_display(textReshaped)
                type += "(" + textDisplay + ")"

            draw.text(x=5,y=y_value,body=type)
            draw.gravity = "north_east"
            draw.text(x=5,y=y_value - 25,body=str(format(float(ii['amount']), '.2f')))
            draw.gravity = "forget"


    #TOTAL AMOUNT
    textReshaped = arabic_reshaper.reshape("المبلغ الاجمالي")
    textDisplayTA = get_display(textReshaped)
    draw.text(x=5,y=y_value + 35,body="Total Amount(" + textDisplayTA + ")")
    draw.gravity = "north_east"
    draw.text(x=5,y=y_value + 5,body=str(format(float(for_printing['total_amount']), '.2f')))
    draw.gravity = "forget"

    #CHANGE
    if type_of_printing != "Bill":
        textReshaped = arabic_reshaper.reshape("الباقي")
        textDisplayChange = get_display(textReshaped)
        draw.text(x=5,y=y_value + 70,body="Change(" + textDisplayChange+")")
        draw.gravity = "north_east"
        draw.text(x=5,y=y_value + 43,body=str(format(float(for_printing['change']), '.2f')))
        draw.gravity = "forget"

        draw.text(x=5,y=y_value+105,body="=====================================")

    #FOOTER ==========

    if for_printing['footer']:
        footer_value = y_value+105
        for x in for_printing['footer'].split("\n"):
            y_value = y_value + 35
            footer_value = footer_value + 25
            draw.text_alignment = "center"
            draw.text(x=300,y=footer_value,body=x)

    im = wImage(width=printWidth, height=height, background=wColor('#ffffff'))
    draw(im)
    im.save(filename=tmpImage)

    basewidth = 385
    baseheight = 222

    img = Image.open('testLogo.png')
    wpercent = (basewidth / float(img.size[0]))
    img = img.resize((basewidth, 350), PIL.Image.ANTIALIAS)
    img.save('testLogo.png')

    # Print an image with your printer library
    printertest = printer.File(port_serial)
    printertest.set(align="left")
    printertest.image('testLogo.png')
    printertest.image(tmpImage)
    printertest.cut()


    print("SAMOKA GYUD Oi")
    bluetoothSerial.close()
    return {}


