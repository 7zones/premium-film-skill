// Round portrait cut-outs, all framed the same way (macOS only): swift tools/mac/portraits.swift <in-dir> <out-dir> [size=768]
// Each headshot is lifted from its backdrop with Apple's subject segmentation (the model behind
// "lift subject" in Photos), then framed the same way for every person: the face (Vision face box)
// is 30% of the square, the top of the hair sits 12% below the top edge, and the crop never runs
// past the bottom of the photo, so no head or shoulder line is cut inside the circle.
import AppKit
import CoreImage
import Vision

let args = CommandLine.arguments
let inDir = URL(fileURLWithPath: args[1])
let outDir = URL(fileURLWithPath: args[2])
let size = args.count > 3 ? Int(args[3])! : 768
let ctx = CIContext()

func rgba(_ img: CGImage) -> (data: [UInt8], w: Int, h: Int) {
  let w = img.width, h = img.height
  var data = [UInt8](repeating: 0, count: w * h * 4)
  let bm = CGContext(data: &data, width: w, height: h, bitsPerComponent: 8, bytesPerRow: w * 4,
                     space: CGColorSpace(name: CGColorSpace.sRGB)!, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
  bm.draw(img, in: CGRect(x: 0, y: 0, width: w, height: h))
  return (data, w, h)
}

let files = try FileManager.default.contentsOfDirectory(at: inDir, includingPropertiesForKeys: nil)
  .filter { ["jpg", "jpeg", "png"].contains($0.pathExtension.lowercased()) }
  .sorted { $0.lastPathComponent < $1.lastPathComponent }

for url in files {
  guard let src = NSImage(contentsOf: url)?.cgImage(forProposedRect: nil, context: nil, hints: nil) else { continue }
  let handler = VNImageRequestHandler(cgImage: src)
  let lift = VNGenerateForegroundInstanceMaskRequest()
  let faces = VNDetectFaceRectanglesRequest()
  try handler.perform([lift, faces])
  guard let obs = lift.results?.first else { print("no subject:", url.lastPathComponent); continue }
  let buf = try obs.generateMaskedImage(ofInstances: obs.allInstances, from: handler, croppedToInstancesExtent: false)
  let cut = ctx.createCGImage(CIImage(cvPixelBuffer: buf), from: CGRect(x: 0, y: 0, width: src.width, height: src.height))!
  let (px, w, h) = rgba(cut)

  // largest face, in top-left pixel coordinates
  guard let face = (faces.results ?? []).max(by: { $0.boundingBox.width < $1.boundingBox.width }) else { print("no face:", url.lastPathComponent); continue }
  let fb = face.boundingBox
  let fx0 = Int(fb.minX * CGFloat(w)), fx1 = Int(fb.maxX * CGFloat(w))
  let fh = fb.height * CGFloat(h)
  let fcx = fb.midX * CGFloat(w)
  // top of the hair: first row with solid subject pixels above the face's span
  var top = Int((1 - fb.maxY) * CGFloat(h))
  scan: for y in 0..<h {
    var solid = 0
    for x in max(0, fx0)..<min(w, fx1) where px[(y * w + x) * 4 + 3] > 140 { solid += 1 }
    if solid > max(3, (fx1 - fx0) / 20) { top = y; break scan }
  }
  let S = min(fh / 0.30, (CGFloat(h) - CGFloat(top)) / 0.88)
  let cropTop = CGFloat(top) - 0.12 * S
  let cropLeft = fcx - S / 2

  let k = CGFloat(size) / S
  var outPx = [UInt8](repeating: 0, count: size * size * 4)
  let out = CGContext(data: &outPx, width: size, height: size, bitsPerComponent: 8, bytesPerRow: size * 4,
                      space: CGColorSpace(name: CGColorSpace.sRGB)!, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
  out.interpolationQuality = .high
  // CGContext origin is bottom-left: place the cut-out so the crop window fills the canvas
  out.draw(cut, in: CGRect(x: -cropLeft * k, y: (cropTop + S - CGFloat(h)) * k, width: CGFloat(w) * k, height: CGFloat(h) * k))
  let rep = NSBitmapImageRep(cgImage: out.makeImage()!)
  let name = url.deletingPathExtension().lastPathComponent + ".png"
  try rep.representation(using: .png, properties: [:])!.write(to: outDir.appendingPathComponent(name))
  print(name, "face", Int(fh), "top", top, "S", Int(S))
}
