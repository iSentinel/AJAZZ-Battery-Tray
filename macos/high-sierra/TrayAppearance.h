#import <AppKit/AppKit.h>

static inline NSArray<NSString *> *AppearanceChoices(void) {
    return @[@"orange", @"white", @"black", @"blue"];
}

static inline NSString *AppearanceChoice(NSString *key) {
    NSString *value = [[NSUserDefaults standardUserDefaults] stringForKey:key];
    return [AppearanceChoices() containsObject:value] ? value : @"orange";
}

static inline BOOL AppearanceMouseStyle(void) {
    NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
    return ![defaults objectForKey:@"MouseTrayIcon"] || [defaults boolForKey:@"MouseTrayIcon"];
}

static inline NSImage *AppearanceAppIcon(NSString *color) {
    if (![AppearanceChoices() containsObject:color]) return nil;
    NSString *file = [color isEqualToString:@"orange"] ? @"AppIcon" :
        [@"AppIcon-" stringByAppendingString:color];
    NSString *path = [[NSBundle mainBundle] pathForResource:file ofType:@"icns"];
    return path ? [[NSImage alloc] initWithContentsOfFile:path] : nil;
}

static inline NSColor *AppearanceColor(NSString *color, NSInteger level) {
    if (level < 0 || level > 100) return NSColor.grayColor;
    if (level <= 10) return [NSColor colorWithSRGBRed:.86 green:.21 blue:.27 alpha:1];
    if (level <= 20) return [NSColor colorWithSRGBRed:.88 green:.57 blue:.07 alpha:1];
    if ([color isEqualToString:@"white"]) return [NSColor colorWithWhite:.95 alpha:1];
    if ([color isEqualToString:@"black"]) return [NSColor colorWithWhite:.13 alpha:1];
    if ([color isEqualToString:@"blue"]) return [NSColor colorWithSRGBRed:.14 green:.39 blue:.78 alpha:1];
    return [NSColor colorWithSRGBRed:.96 green:.47 blue:.09 alpha:1];
}

static inline NSImage *AppearanceTrayImage(NSInteger level, NSString *color, BOOL mouseStyle) {
    BOOL valid = level >= 0 && level <= 100;
    BOOL mouse = mouseStyle && valid && level > 20;
    NSSize size = NSMakeSize(mouse ? 18 : 36, 18);
    NSColor *background = AppearanceColor(color, level);
    NSImage *image = [NSImage imageWithSize:size flipped:NO drawingHandler:^BOOL(NSRect rect) {
        NSBezierPath *body = [NSBezierPath bezierPathWithRoundedRect:NSInsetRect(rect, mouse ? 3 : 1, 1)
            xRadius:mouse ? 6 : 5 yRadius:mouse ? 6 : 5];
        [background setFill];
        [body fill];
        [[NSColor colorWithWhite:.65 alpha:1] setStroke];
        body.lineWidth = .8;
        [body stroke];
        if (mouse) {
            [NSColor.darkGrayColor setStroke];
            NSBezierPath *seams = [NSBezierPath bezierPath];
            [seams moveToPoint:NSMakePoint(9, 16)];
            [seams lineToPoint:NSMakePoint(9, 10)];
            [seams moveToPoint:NSMakePoint(3, 10)];
            [seams lineToPoint:NSMakePoint(15, 10)];
            seams.lineWidth = 1;
            [seams stroke];
        } else {
            NSString *text = valid ? [NSString stringWithFormat:@"%ld%%", (long)level] : @"?";
            NSMutableParagraphStyle *paragraph = [[NSMutableParagraphStyle alloc] init];
            paragraph.alignment = NSTextAlignmentCenter;
            NSColor *foreground = [color isEqualToString:@"white"] && level > 20 && valid
                ? NSColor.blackColor : NSColor.whiteColor;
            [text drawInRect:NSMakeRect(0, 2, size.width, 15) withAttributes:@{
                NSFontAttributeName: [NSFont boldSystemFontOfSize:11],
                NSForegroundColorAttributeName: foreground,
                NSParagraphStyleAttributeName: paragraph}];
        }
        return YES;
    }];
    image.template = NO;
    return image;
}

static inline BOOL AppearanceHasRed(NSBitmapImageRep *bitmap) {
    for (NSInteger x = 0; x < bitmap.pixelsWide; x++) {
        for (NSInteger y = 0; y < bitmap.pixelsHigh; y++) {
            NSColor *pixel = [[bitmap colorAtX:x y:y]
                colorUsingColorSpace:[NSColorSpace deviceRGBColorSpace]];
            if (pixel && pixel.alphaComponent > .8 && pixel.redComponent > .75 &&
                pixel.greenComponent < .35 && pixel.blueComponent < .4) return YES;
        }
    }
    return NO;
}

static inline BOOL AppearanceSelfTest(void) {
    for (NSString *choice in AppearanceChoices()) {
        if (!AppearanceAppIcon(choice).valid) return NO;
        for (NSNumber *value in @[@0, @8, @10, @11, @20, @21, @100, @(-1), @101]) {
            NSInteger level = value.integerValue;
            NSImage *image = AppearanceTrayImage(level, choice, YES);
            NSSize expected = NSMakeSize(level > 20 && level <= 100 ? 18 : 36, 18);
            NSData *bytes = image.TIFFRepresentation;
            NSBitmapImageRep *bitmap = bytes ? [NSBitmapImageRep imageRepWithData:bytes] : nil;
            if (!NSEqualSizes(image.size, expected) || image.template || !bitmap) return NO;
            if (AppearanceHasRed(bitmap) != (level >= 0 && level <= 10)) return NO;
        }
    }
    return AppearanceAppIcon(@"../invalid") == nil;
}
