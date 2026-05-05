# Face Detection Tips

## How to Upload Images Successfully

### ✅ Good Image Examples:
- **Clear front-facing face**: Person looking directly at camera
- **Good lighting**: Face is well-lit, not in shadow
- **High quality**: Image is clear, not blurry or pixelated
- **Single person**: One clear face in the image
- **No obstructions**: Face not covered by masks, sunglasses, or hands
- **Proper size**: Face takes up reasonable portion of image (not too small)

### ❌ Common Issues:

1. **No Face Detected Error**
   - **Cause**: Face not clear enough, wrong angle, or poor quality
   - **Solution**: Use a clear front-facing photo with good lighting

2. **Side Profile or Angle**
   - **Cause**: Face detection works best with front-facing images
   - **Solution**: Use a photo where person is looking at the camera

3. **Poor Lighting**
   - **Cause**: Face too dark or too bright
   - **Solution**: Use image with even, natural lighting

4. **Low Resolution**
   - **Cause**: Image too small or compressed
   - **Solution**: Use higher quality image (at least 200x200 pixels for face)

5. **Multiple Faces**
   - **Cause**: Multiple people in image
   - **Solution**: System will use the first/largest face detected

## Image Requirements

- **Format**: JPG, PNG, JPEG, GIF, BMP
- **Size**: Recommended at least 500x500 pixels
- **Face Size**: Face should be at least 100x100 pixels in the image
- **Orientation**: Any orientation (system auto-rotates if needed)

## Testing Your Image

Before uploading, check:
1. Can you clearly see the person's face?
2. Is the face front-facing (not profile)?
3. Is the lighting good?
4. Is the image clear (not blurry)?

## After Upload

Once you successfully upload a missing person:
1. ✅ The system will store their face embedding
2. ✅ Start the live feed detection
3. ✅ System will automatically detect this person in the camera feed
4. ✅ Alerts and snapshots will be generated when detected

## Troubleshooting

**Still getting "No face detected"?**

1. Try a different image of the same person
2. Crop the image to focus on the face
3. Adjust brightness/contrast if needed
4. Ensure the image file is not corrupted
5. Try converting to JPG format

**The system tries multiple detection methods automatically:**
- OpenCV (fastest)
- SSD (more accurate)
- Dlib (good for various angles)
- MTCNN (very accurate)
- RetinaFace (most accurate)

If one fails, it automatically tries the next one!
