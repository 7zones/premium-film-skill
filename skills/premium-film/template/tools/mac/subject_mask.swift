// The person in a photo as a soft mask (macOS only): swift tools/mac/subject_mask.swift <photo> <mask.png>
// Apple's subject segmentation (the model behind "lift subject" in Photos), at the photo's own size:
// white = the person and what they hold, black = everything behind them.
import AppKit
import CoreImage
import Vision

let args = CommandLine.arguments
let src = NSImage(contentsOf: URL(fileURLWithPath: args[1]))!.cgImage(forProposedRect: nil, context: nil, hints: nil)!
let handler = VNImageRequestHandler(cgImage: src)
let lift = VNGenerateForegroundInstanceMaskRequest()
try handler.perform([lift])
guard let obs = lift.results?.first else { print("no subject"); exit(1) }
let buf = try obs.generateScaledMaskForImage(forInstances: obs.allInstances, from: handler)
let ci = CIImage(cvPixelBuffer: buf)
let ctx = CIContext()
let gray = ctx.createCGImage(ci, from: ci.extent, format: .L8, colorSpace: CGColorSpace(name: CGColorSpace.linearGray)!)!
let rep = NSBitmapImageRep(cgImage: gray)
try rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: args[2]))
print("mask", gray.width, "x", gray.height)
