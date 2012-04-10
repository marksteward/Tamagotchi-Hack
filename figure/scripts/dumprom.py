#!/usr/bin/env python
import os
import Image

f = open("../ROMDump/rom.bin", 'rb')
a = f.read()

def getnum(bytes):
  num = 0
  for i, b in enumerate(bytes):
    num |= ord(b) << 8 * i
  return num

def dumpimage(d, num, base, o):
  print '  Loading image %d at 0x%06x' % (num, o + base)

  width = ord(a[o + base])
  height = ord(a[o + base + 1])

  if (width, height) == (1, 1):
    print '    Placeholder image found'
    return None

  if not 0 < width <= 0x60:
    raise Exception('Invalid width %d at 0x%06x' % (width, o))

  if not 0 < height <= 0x60:
    raise Exception('Invalid height %d at 0x%06x' % (height, o))

  print '   %04d: %dx%d' % (num, width, height)

  if width % 4:
    width += 4 - width % 4

    print "   Padded to %dx%d" % (width, height)

  s = ""
  # Why + 1?
  for i in range(0, height*width/4 + 1):
    for j in range(0, 4):
      #print ord(a[i])
      #print (0x03 << ((3- j)*2))
      k = ord(a[i + o + base + 2]) & (0x03 << ((3 - j)*2))

      l = (k >> ((3-j)*2))
    
      s += chr(0xFF&(~(l*(255/4))))

  #print s
  image = Image.fromstring("L", (width, height), s, "raw", "L")
  image.save("%s/%04d-0x%06x.png" % (d, num, base + o), 'PNG')

  o += height*width/4
  #print 'Next image at 0x%06x' % o
  return o


def dumpdir(d, num, base, start, end):
  print ' Loading dir %d at 0x%06x' % (num, start + base)

  d = '%s/%04d-%06x' % (d, num, start + base)
  if not os.path.exists(d):
    os.makedirs(d)

  o = start
  num = 0
  while o < end:
    addr = getnum(a[o + base:o + base + 3])

    nextaddr = dumpimage(d, num, base, addr)

    o += 3
    num += 1

    if not nextaddr:
      print '  Readed end of dir, 0x%x remaining' % (end - o)
      return

  # Heuristic until a better way to determine the length is found
  print '  Reached beginning of next section, 0x%x remaining' % (end - o)


def dumpsegment(d, num, base):
  print 'Loading segment %d at 0x%06x' % (num, base)

  d = '%s/%04d-%06x' % (d, num, base)
  if not os.path.exists(d):
    os.makedirs(d)

  # This is presumably considered reserved space in the segment header
  diskheader = a[base:base + 0xf]
  if any(map(ord, diskheader)):
    print ' Disk header: %s' % ' '.join(hex(ord(b)) for b in diskheader)

  header = a[base + 0x10:base + 0x1f]
  print ' Segment header: %s' % ' '.join(hex(ord(b)) for b in header)

  if header[0:2] != '\xaa\x55':
    raise Exception('Invalid magic/signature')

  o = 0x10
  base += len(header)

  sections = []
  while True:
    addr = getnum(a[o + base:o + base + 3])
    if not addr:
      break

    sections.append(addr)
    o += 3

  sections.sort()

  for i in range(len(sections)):
    start = sections[i]
    if i == len(sections) - 1:
      end = 0x55550
    else:
      end = sections[i + 1]

    try:
      nextimg = dumpdir(d, i, base, start, end)
    except Exception, e:
      print repr(e)



dumpsegment('dump', 0, 0)
dumpsegment('dump', 1, 0x55550)
dumpsegment('dump', 2, 0xaaaa0)


