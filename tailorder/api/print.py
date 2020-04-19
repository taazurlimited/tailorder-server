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
from pathlib import Path

@api.route('/print_receipt', methods=['POST'])
def print_receipt():
    receipt_from_tailpos = loads(request.get_data(as_text=True))
    for_printing = receipt_from_tailpos['data']
    type_of_printing = receipt_from_tailpos['type']
    print(for_printing)

    port_serial = "/dev/rfcomm0"
    home = str(Path.home())
    print(home)
    bluetoothSerial = serial.Serial(port_serial, baudrate=115200, timeout=1)
    company_name = for_printing['company'].lower().replace(" ", "_")
    print(company_name)
    fontPath = home + "/tailorder-server/fonts/" + company_name + ".ttf"
    print(fontPath)
    tmpImage = 'print_images/receipt.png'
    #printWidth = 375
    printWidth = 570

    height = 500
    draw = wDrawing()
    draw.font = fontPath

    #COMPANY ==============
    company_translation = ""
    if for_printing['companyTranslation']:
        textReshaped = arabic_reshaper.reshape(for_printing['companyTranslation'])
        company_translation = get_display(textReshaped)
    draw.font_size = 34
    y_value = 30
    draw.text(x=180,y=y_value,body=for_printing['company'])
    draw.text(x=180,y=y_value + 35,body=company_translation)

    y_value = y_value + 45
    draw.font_size = 26

    #HEADER ==========
    if for_printing['header']:
        draw.text_alignment = "center"
        header_value = y_value
        header_array = for_printing['header'].split("\n")
        header_array_translation = for_printing['headerTranslation'].split("\n")

        for x in range(0,len(header_array)):
            if header_array[x]:
                translation = ""
                if x < len(header_array_translation) and  header_array_translation[x]:
                    textReshaped = arabic_reshaper.reshape(header_array_translation[x])
                    translation = get_display(textReshaped)

                y_value = y_value + 40
                header_value = header_value + 25

                draw.text(x=300,y=header_value,body=header_array[x] + translation)

    draw.text_alignment = "undefined"
    if for_printing['vat_number']:
        y_value = y_value + 35
        header_value = header_value + 25
        draw.text(x=5,y=y_value,body="VAT No.: " + for_printing['vat_number'])

    if for_printing['ticket_number']:
        header_value = header_value + 25
        draw.text(x=330,y=y_value,body="Ticket Number: " +  for_printing['ticket_number'])

    y_value = y_value + 35

    #DATE ==================
    split_date = for_printing['date'].split()
    draw.font_size = 26
    draw.text(x=5,y=y_value,body=split_date[0])
    draw.gravity = "north_east"
    draw.text(x=5,y=y_value - 20,body=split_date[1])
    draw.gravity = "forget"

    y_value = y_value + 35

    #ORDER TYPE ==============
    draw.font_size = 26
    draw.text(x=5,y=y_value,body="Order Type: " +  for_printing['ordertype'])

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
                translation_text = textDisplay

                draw.text(x=5,y=y_value,body=translation_text)

        else:
            y_value = y_value + 35
            draw.text(x=5,y=y_value,body=i['item_name'] )
            if i['translation_text']:
                y_value = y_value + 35
                textReshaped = arabic_reshaper.reshape(i['translation_text'])
                textDisplay = get_display(textReshaped)
                translation_text = textDisplay
                draw.text(x=5,y=y_value,body= translation_text)


    draw.text(x=5,y=y_value+35,body="=====================================")

    y_value = y_value + 35

    #SUBTOTAL
    textReshaped = arabic_reshaper.reshape("المبلغ الاجمالي")
    textDisplaySubtotal = get_display(textReshaped)
    draw.text(x=5,y=y_value + 35,body="Subtotal"+ textDisplaySubtotal)
    draw.gravity = "north_east"
    draw.text(x=5,y=y_value + 5,body=for_printing['subtotal'])
    draw.gravity = "forget"

    y_value = y_value + 35

    #DISCOUNT
    textReshaped = arabic_reshaper.reshape("الخصم")
    textDisplayDiscount = get_display(textReshaped)
    draw.text(x=5,y=y_value + 35,body="Discount" + textDisplayDiscount)
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
            tax_translation = ""
            if iii['translation']:
                height += 35
                textReshaped = arabic_reshaper.reshape(iii['translation'])
                tax_translation = get_display(textReshaped)

            draw.text(x=5,y=y_value,body=iii['name'] + tax_translation)
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
                type += textDisplay

            draw.text(x=5,y=y_value,body=type)
            draw.gravity = "north_east"
            draw.text(x=5,y=y_value - 25,body=str(format(float(ii['amount']), '.2f')))
            draw.gravity = "forget"


    #TOTAL AMOUNT
    height += 35
    textReshaped = arabic_reshaper.reshape("المبلغ الاجمالي")
    textDisplayTA = get_display(textReshaped)
    draw.text(x=5,y=y_value + 35,body="Total Amount" + textDisplayTA)
    draw.gravity = "north_east"
    draw.text(x=5,y=y_value + 5,body=str(format(float(for_printing['total_amount']), '.2f')))
    draw.gravity = "forget"

    #CHANGE
    if type_of_printing != "Bill":
        height += 35
        textReshaped = arabic_reshaper.reshape("الباقي")
        textDisplayChange = get_display(textReshaped)
        draw.text(x=5,y=y_value + 70,body="Change" + textDisplayChange)
        draw.gravity = "north_east"
        draw.text(x=5,y=y_value + 43,body=str(format(float(for_printing['change']), '.2f')))
        draw.gravity = "forget"

    draw.text(x=5,y=y_value+105,body="=====================================")

    #FOOTER ==========

    if for_printing['footer']:
        footer_value = y_value+105
        footer_array = for_printing['footer'].split("\n")
        print(footer_array)
        footer_array_translation = for_printing['footerTranslation'].split("\n")
        for xx in range(0,len(footer_array)):
            translation = ""
            if footer_array[xx]:
                height += 35
                if xx < len(footer_array_translation) and footer_array_translation[xx]:
                    textReshaped = arabic_reshaper.reshape(footer_array_translation[xx])
                    translation = get_display(textReshaped)
                y_value = y_value + 35
                footer_value = footer_value + 25
                draw.text_alignment = "center"
                draw.text(x=300,y=footer_value,body=footer_array[xx] + translation)
    height += 35
    im = wImage(width=printWidth, height=height, background=wColor('#ffffff'))
    draw(im)
    im.save(filename=tmpImage)

    basewidth = 230
    baseheight = 221
    logo = "logos/logo.png"
    img = Image.open(logo)
    wpercent = (basewidth / float(img.size[0]))
    img = img.resize((basewidth, baseheight), PIL.Image.ANTIALIAS)
    img.save(logo)

    # Print an image with your printer library
    printertest = printer.File(port_serial)
    printertest.set(align="center")
    printertest.image(logo)
    printertest.image(tmpImage)
    printertest.cut()

    bluetoothSerial.close()

    return {}


@api.route('/print_report', methods=['POST'])
def print_report():

    receipt_from_tailpos = loads(request.get_data(as_text=True))
    for_printing = receipt_from_tailpos['data']
    type_of_printing = receipt_from_tailpos['type']
    print(for_printing)

    port_serial = "/dev/rfcomm0"
    home = str(Path.home())
    bluetoothSerial = serial.Serial(port_serial, baudrate=115200, timeout=1)
    company_name = for_printing['company'].lower().replace(" ", "_")
    print(company_name)
    fontPath = home + "/tailorder-server/fonts/" + company_name + ".ttf"
    print(fontPath)
    tmpImage = 'print_images/report.png'
    printWidth = 570

    height = 600
    draw = wDrawing()
    draw.font = fontPath

    #COMPANY ==============
    draw.font_size = 34
    y_value = 30
    draw.text(x=180,y=y_value,body=for_printing['company'])
    draw.font_size = 26

    y_value = y_value + 35


    draw.text(x=5,y=y_value ,body="=====================================")

    y_value = y_value + 35

    draw.text_alignment = "center"

    draw.text(x=300,y=y_value ,body=for_printing['reportType'])

    draw.text_alignment = "undefined"

    y_value = y_value + 35

    draw.text(x=5,y=y_value ,body="=====================================")

    y_value = y_value + 35

    draw.text(x=5,y=y_value ,body="Opened: " + for_printing['opened'])

    y_value = y_value + 35

    draw.text(x=5,y=y_value ,body="Opened: " + for_printing['closed'])

    y_value = y_value + 35

    draw.text(x=5,y=y_value ,body="=====================================")

    y_value = y_value + 35
    labels = [
        "Opening Amount",
        "Expected Drawer",
        "Actual Money",
        ]
    for i in labels:
        draw.text(x=5,y=y_value ,body=i)
        draw.gravity ="north_east"
        draw.text(x=5,y=y_value - 35 ,body=for_printing[i.lower().replace(" ","_")])
        draw.gravity = "forget"
        y_value = y_value + 35

    draw.text(x=5,y=y_value ,body=for_printing['short_or_overage'])
    draw.gravity ="north_east"
    draw.text(x=5,y=y_value - 35 ,body=for_printing["short_or_overage_amount"])
    draw.gravity = "forget"

    y_value = y_value + 35

    draw.text(x=5,y=y_value ,body="=====================================")

    y_value = y_value + 35

    labels = [
        "Cash Sales",
        "Total Net Sales",
        "Total Net Sales with Vat",
        "Payouts",
        "Payins",

        ]
    for i in labels:
        draw.text(x=5,y=y_value ,body=i)
        draw.gravity ="north_east"
        draw.text(x=5,y=y_value - 35 ,body=for_printing[i.lower().replace(" ","_")])
        draw.gravity = "forget"
        y_value = y_value + 35

    if len(for_printing['total_taxes']) > 0:
        for i in for_printing['total_taxes']:
            height += 35
            draw.text(x=5,y=y_value ,body=i['name'])
            draw.gravity ="north_east"
            draw.text(x=5,y=y_value - 35 ,body=str(i['totalAmount']))
            draw.gravity = "forget"
            y_value = y_value + 35


    labels = [
        "Discount",
        "Cancelled",
        "Voided",
        "Transactions",
        ]
    for i in labels:
        height += 35
        draw.text(x=5,y=y_value ,body=i)
        draw.gravity ="north_east"
        draw.text(x=5,y=y_value - 35 ,body=for_printing[i.lower().replace(" ","_")])
        draw.gravity = "forget"
        y_value = y_value + 35
    height += 35
    draw.text(x=5,y=y_value ,body="=====================================")

    y_value = y_value + 35
    labels = [
        "Dine in",
        "Takeaway",
        "Delivery",
        "Online",
        "Family",
        ]
    for i in labels:
        if float(for_printing[i.lower().replace(" ","_")]) > 0:
            height += 35
            draw.text(x=5,y=y_value ,body=i)
            draw.gravity ="north_east"
            draw.text(x=5,y=y_value - 35 ,body=for_printing[i.lower().replace(" ","_")])
            draw.gravity = "forget"
            y_value = y_value + 35

    if len(for_printing['categories_total_amounts']) > 0:
        for i in for_printing['categories_total_amounts']:
            height += 35
            draw.text(x=5,y=y_value ,body=i['name'])
            draw.gravity ="north_east"
            draw.text(x=5,y=y_value - 35 ,body=str(format(float(i['total_amount']), '.2f')))
            draw.gravity = "forget"
            y_value = y_value + 35
    else:
        y_value = y_value + 35
    height += 35
    draw.text(x=5,y=y_value ,body="=====================================")
    y_value = y_value + 35

    if len(for_printing['mop_total_amounts']) > 0:
        for i in for_printing['mop_total_amounts']:
            height += 35
            draw.text(x=5,y=y_value ,body=i['name'])
            draw.gravity ="north_east"
            draw.text(x=5,y=y_value - 35 ,body=str(format(float(i['total_amount']), '.2f')))
            draw.gravity = "forget"
            y_value = y_value + 35
    if len(for_printing['mop_total_amounts']) > 0:
        height += 35

        draw.text(x=5,y=y_value ,body="=====================================")

    im = wImage(width=printWidth, height=height, background=wColor('#ffffff'))
    draw(im)
    im.save(filename=tmpImage)


    basewidth = 230
    baseheight = 221
    logo = "logos/logo.png"
    img = Image.open(logo)
    wpercent = (basewidth / float(img.size[0]))
    img = img.resize((basewidth, baseheight), PIL.Image.ANTIALIAS)
    img.save(logo)

    # Print an image with your printer library
    printertest = printer.File(port_serial)
    printertest.set(align="center")
    printertest.image(logo)
    printertest.image(tmpImage)
    printertest.cut()

    bluetoothSerial.close()

    return {}
