from decimal import Decimal
from qrcodegen import *

def generate_upn_qr(name, address1, address2, amount, reference, purpose):
  name = name.strip()
  address1 = address1.strip()
  address2 = address2.strip()
  amount = str(int(amount * 100)).zfill(11)
  reference = reference.replace(' ', '')
  purpose = purpose.strip()

  iban = 'SI56 6100 0000 5740 710'.replace(' ', '')
  to_name = 'Danes je nov dan'.strip()
  to_address1 = 'Parmova 20'.strip()
  to_address2 = '1000 Ljubljana'.strip()

  textLines = [
      'UPNQR',
      '',
      '',
      '',
      '',
      name,
      address1,
      address2,
      amount,
      '',
      '',
      'GDSV',
      purpose,
      '',
      iban,
      reference,
      to_name,
      to_address1,
      to_address2,
  ]
  qrText = ('\n'.join(textLines) + '\n').encode('iso-8859-2', errors='ignore')
  qrText += (str(len(qrText)) + '\n').encode('iso-8859-2', errors='ignore')

  eci_segment = QrSegment.make_eci(4)
  text_segment = QrSegment.make_bytes(qrText)
  qr1 = QrCode.encode_segments([eci_segment, text_segment], QrCode.Ecc.MEDIUM, 15, 15, 2, False)
  return qr1.to_svg_str(2)

# print(generate_upn_qr('Tomaž Kunst', 'Zeče pri Bucah 15a', '1000 Ljubljana', Decimal('14.00'), 'SI05 0000000058', 'Poloznica za račun st. 58'))
