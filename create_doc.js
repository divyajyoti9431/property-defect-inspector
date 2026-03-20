const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, LevelFormat
} = require('docx');
const fs = require('fs');

// Colors
const DARK_BLUE = "1F4E79";
const GRAY_HEADER = "D9D9D9";
const CODE_BG = "F2F2F2";

// Page content width: 12240 - 1440 - 1440 = 9360 DXA
const CONTENT_WIDTH = 9360;

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, bold: true, color: DARK_BLUE, font: "Arial", size: 28 })]
  });
}

function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text, bold: true, font: "Arial", size: 24 })]
  });
}

function para(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({ text, font: "Arial", size: 22, ...opts })]
  });
}

function bullet(text, numbered = false, level = 0) {
  return new Paragraph({
    numbering: { reference: numbered ? "numbers" : "bullets", level },
    children: [new TextRun({ text, font: "Arial", size: 22 })]
  });
}

function spacer() {
  return new Paragraph({ children: [new TextRun("")] });
}

function codeBlock(lines) {
  const paragraphs = lines.map(line =>
    new Paragraph({
      children: [new TextRun({ text: line, font: "Courier New", size: 18 })]
    })
  );
  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: [CONTENT_WIDTH],
    rows: [
      new TableRow({
        children: [
          new TableCell({
            borders,
            width: { size: CONTENT_WIDTH, type: WidthType.DXA },
            shading: { fill: CODE_BG, type: ShadingType.CLEAR },
            margins: { top: 80, bottom: 80, left: 160, right: 160 },
            children: paragraphs
          })
        ]
      })
    ]
  });
}

function makeTable(headerCells, rows, colWidths) {
  const totalWidth = colWidths.reduce((a, b) => a + b, 0);
  const headerRow = new TableRow({
    children: headerCells.map((cell, i) =>
      new TableCell({
        borders,
        width: { size: colWidths[i], type: WidthType.DXA },
        shading: { fill: GRAY_HEADER, type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({ children: [new TextRun({ text: cell, bold: true, font: "Arial", size: 20 })] })]
      })
    )
  });

  const dataRows = rows.map(row =>
    new TableRow({
      children: row.map((cell, i) =>
        new TableCell({
          borders,
          width: { size: colWidths[i], type: WidthType.DXA },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [new TextRun({ text: cell, font: "Arial", size: 20 })] })]
        })
      )
    })
  );

  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [headerRow, ...dataRows]
  });
}

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      },
      {
        reference: "numbers",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      }
    ]
  },
  styles: {
    default: {
      document: { run: { font: "Arial", size: 22 } }
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: DARK_BLUE },
        paragraph: { spacing: { before: 300, after: 120 }, outlineLevel: 0 }
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 1 }
      }
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "Page ", font: "Arial", size: 18 }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 18 }),
            new TextRun({ text: " of ", font: "Arial", size: 18 }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], font: "Arial", size: 18 })
          ]
        })]
      })
    },
    children: [
      // TITLE
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 480, after: 120 },
        children: [new TextRun({ text: "PTU-Based Laser Pointing System", bold: true, color: DARK_BLUE, font: "Arial", size: 52 })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 480 },
        children: [new TextRun({ text: "From Reactive to Predictive Tracking — Complete Project Plan & Pipeline", font: "Arial", size: 26, color: "555555" })]
      }),

      // SECTION 1
      heading1("SECTION 1: PROJECT OVERVIEW"),

      heading2("1.1 Objective"),
      para("Replace the existing reactive \"reduce-the-distance\" PTU tracking logic with a predictive, Kalman Filter-based algorithm to achieve \u226580% laser-on-drone time during active movement."),
      spacer(),

      heading2("1.2 Existing Infrastructure (Do Not Modify)"),
      bullet("Working UI (User Interface)"),
      bullet("Camera integration with 36x optical zoom"),
      bullet("PTU (Pan-Tilt Unit) hardware control"),
      bullet("YOLOv8-based drone detection pipeline"),
      bullet("Basic reactive tracking loop"),
      spacer(),

      heading2("1.3 Success Criteria"),
      makeTable(
        ["Metric", "Target"],
        [
          ["Drone speed handled", "Up to 1 m/s"],
          ["Drone distance", "Up to 50 meters"],
          ["Laser on-target rate", "\u226580% during movement"],
          ["System latency", "Minimized to meet 80% target"]
        ],
        [4680, 4680]
      ),
      spacer(),

      // SECTION 2
      new Paragraph({ children: [new PageBreak()] }),
      heading1("SECTION 2: CURRENT SYSTEM ANALYSIS (Phase 1)"),

      heading2("2.1 Reactive Tracking \u2014 The Problem"),
      para("Current logic (pseudo-code):"),
      spacer(),
      codeBlock([
        "loop:",
        "    bbox = yolo_detect(frame)",
        "    dx = bbox.center_x - crosshair_x",
        "    dy = bbox.center_y - crosshair_y",
        "    ptu.move(step * sign(dx), step * sign(dy))"
      ]),
      spacer(),
      para("Problems:"),
      bullet("No velocity estimation \u2014 the PTU always reacts to where the drone WAS"),
      bullet("Constant step size causes oscillation near target"),
      bullet("No prediction \u2014 laser lags behind moving drone"),
      bullet("No Kalman smoothing \u2014 noisy detections cause jitter"),
      spacer(),

      heading2("2.2 Latency Sources to Measure"),
      bullet("YOLO inference time (typically 20\u201350 ms on GPU, 80\u2013150 ms on CPU)"),
      bullet("Frame capture/buffer delay"),
      bullet("PTU command round-trip time (serial/TCP)"),
      bullet("Python GIL contention in main loop"),
      spacer(),

      heading2("2.3 Analysis Tasks"),
      bullet("Instrument the existing loop with timestamps at each stage", true),
      bullet("Log: frame_time, detection_time, ptu_command_time, ptu_ack_time", true),
      bullet("Calculate total lag = (ptu_ack_time) - (drone_actual_position_time)", true),
      bullet("Identify the dominant bottleneck", true),
      spacer(),

      // SECTION 3
      new Paragraph({ children: [new PageBreak()] }),
      heading1("SECTION 3: IMPLEMENTATION PLAN (Phase 2)"),

      heading2("3.1 Architecture Overview"),
      para("The new pipeline:"),
      spacer(),
      codeBlock([
        "Camera Frame \u2192 YOLOv8 Detection \u2192 Kalman Filter \u2192 Predictive Lookahead \u2192 Coordinate Transform \u2192 PTU Command"
      ]),
      spacer(),

      heading2("3.2 Component 1 \u2014 Kalman Filter (State Estimator)"),
      para("State vector: [x, y, vx, vy] (pixel position + velocity)"),
      spacer(),
      para("The Kalman Filter will:"),
      bullet("Estimate the drone's true position from noisy YOLO bounding boxes"),
      bullet("Predict the drone's state one step ahead (even when detection fails)"),
      bullet("Smooth out jitter from YOLO fluctuations"),
      spacer(),
      para("Key equations:"),
      bullet("Predict: x\u0302 = F\u00b7x + B\u00b7u (state transition)"),
      bullet("Update: x\u0302 = x\u0302 + K\u00b7(z - H\u00b7x\u0302) (measurement correction)"),
      spacer(),
      para("Recommended library: filterpy (pip install filterpy)"),
      spacer(),

      heading2("3.3 Component 2 \u2014 Predictive Lookahead"),
      para("After the Kalman Filter estimates [x, y, vx, vy], aim at the FUTURE position:"),
      spacer(),
      codeBlock([
        "lookahead_time = system_lag_ms / 1000.0  # measured in Phase 1",
        "predicted_x = kalman_x + vx * lookahead_time",
        "predicted_y = kalman_y + vy * lookahead_time"
      ]),
      spacer(),
      para("The lookahead_time compensates exactly for the measured system lag."),
      spacer(),

      heading2("3.4 Component 3 \u2014 Coordinate Transformation"),
      para("Convert pixel coordinates to PTU pan/tilt angles:"),
      spacer(),
      codeBlock([
        "pan_angle  = (predicted_x - frame_center_x) * (H_FOV / frame_width)",
        "tilt_angle = (predicted_y - frame_center_y) * (V_FOV / frame_height)"
      ]),
      spacer(),
      para("Where:"),
      bullet("H_FOV = horizontal field of view (degrees) at current zoom level"),
      bullet("V_FOV = vertical field of view (degrees) at current zoom level"),
      bullet("These must be calibrated per zoom level (36x zoom \u2248 ~0.5\u00b0 \u00d7 0.3\u00b0 FOV)"),
      spacer(),

      heading2("3.5 Component 4 \u2014 Adaptive Step / PID Controller (Optional Enhancement)"),
      para("Replace fixed step moves with a PID controller:"),
      spacer(),
      codeBlock([
        "error_pan  = target_pan  - current_pan",
        "error_tilt = target_tilt - current_tilt",
        "ptu_pan_cmd  = Kp*error_pan  + Ki*integral_pan  + Kd*derivative_pan",
        "ptu_tilt_cmd = Kp*error_tilt + Ki*integral_tilt + Kd*derivative_tilt"
      ]),
      spacer(),
      para("Benefits:"),
      bullet("Proportional: faster response to large errors"),
      bullet("Integral: eliminates steady-state offset"),
      bullet("Derivative: damping to prevent overshoot"),
      spacer(),

      // SECTION 4
      new Paragraph({ children: [new PageBreak()] }),
      heading1("SECTION 4: COMPLETE CODE PIPELINE"),

      heading2("4.1 File Structure"),
      codeBlock([
        "project/",
        "\u251c\u2500\u2500 tracker/",
        "\u2502   \u251c\u2500\u2500 __init__.py",
        "\u2502   \u251c\u2500\u2500 kalman_tracker.py      \u2190 Kalman Filter wrapper",
        "\u2502   \u251c\u2500\u2500 predictor.py           \u2190 Lookahead logic",
        "\u2502   \u251c\u2500\u2500 coord_transform.py     \u2190 Pixel \u2192 PTU angle",
        "\u2502   \u2514\u2500\u2500 pid_controller.py      \u2190 Optional PID",
        "\u251c\u2500\u2500 main_tracking_loop.py      \u2190 Replace existing loop",
        "\u2514\u2500\u2500 config.py                  \u2190 All tunable parameters"
      ]),
      spacer(),

      heading2("4.2 kalman_tracker.py"),
      codeBlock([
        "import numpy as np",
        "from filterpy.kalman import KalmanFilter",
        "",
        "class DroneKalmanTracker:",
        "    def __init__(self, dt=0.033):  # dt = 1/30 fps",
        "        self.kf = KalmanFilter(dim_x=4, dim_z=2)",
        "        self.dt = dt",
        "        # State: [x, y, vx, vy]",
        "        self.kf.F = np.array([[1,0,dt,0],",
        "                               [0,1,0,dt],",
        "                               [0,0,1, 0],",
        "                               [0,0,0, 1]])",
        "        # Measurement: [x, y]",
        "        self.kf.H = np.array([[1,0,0,0],",
        "                               [0,1,0,0]])",
        "        self.kf.R *= 10    # Measurement noise",
        "        self.kf.Q *= 0.1   # Process noise",
        "        self.initialized = False",
        "",
        "    def update(self, cx, cy):",
        "        if not self.initialized:",
        "            self.kf.x = np.array([cx, cy, 0, 0])",
        "            self.initialized = True",
        "        else:",
        "            self.kf.predict()",
        "            self.kf.update(np.array([cx, cy]))",
        "        return self.kf.x  # [x, y, vx, vy]",
        "",
        "    def predict_only(self):",
        "        \"\"\"Call when detection fails -- extrapolate position\"\"\"",
        "        self.kf.predict()",
        "        return self.kf.x"
      ]),
      spacer(),

      heading2("4.3 predictor.py"),
      codeBlock([
        "class PredictiveLookahead:",
        "    def __init__(self, lag_seconds=0.1):",
        "        self.lag = lag_seconds  # Measured system lag",
        "",
        "    def get_target(self, state):",
        "        x, y, vx, vy = state",
        "        target_x = x + vx * self.lag",
        "        target_y = y + vy * self.lag",
        "        return target_x, target_y"
      ]),
      spacer(),

      heading2("4.4 coord_transform.py"),
      codeBlock([
        "class CoordTransform:",
        "    def __init__(self, frame_w, frame_h, h_fov_deg, v_fov_deg):",
        "        self.fw = frame_w",
        "        self.fh = frame_h",
        "        self.h_fov = h_fov_deg",
        "        self.v_fov = v_fov_deg",
        "",
        "    def pixel_to_angle(self, px, py):",
        "        cx, cy = self.fw / 2, self.fh / 2",
        "        pan   = (px - cx) / self.fw * self.h_fov",
        "        tilt  = (py - cy) / self.fh * self.v_fov",
        "        return pan, tilt"
      ]),
      spacer(),

      heading2("4.5 main_tracking_loop.py (New Logic)"),
      codeBlock([
        "tracker = DroneKalmanTracker(dt=1/fps)",
        "predictor = PredictiveLookahead(lag_seconds=measured_lag)",
        "transform = CoordTransform(1920, 1080, h_fov=0.5, v_fov=0.3)",
        "",
        "while True:",
        "    frame = camera.get_frame()",
        "    detections = yolo.detect(frame)",
        "",
        "    if detections:",
        "        cx, cy = get_bbox_center(detections[0])",
        "        state = tracker.update(cx, cy)",
        "    else:",
        "        state = tracker.predict_only()  # Coasting",
        "",
        "    if tracker.initialized:",
        "        target_x, target_y = predictor.get_target(state)",
        "        pan, tilt = transform.pixel_to_angle(target_x, target_y)",
        "        ptu.move_absolute(pan, tilt)"
      ]),
      spacer(),

      // SECTION 5
      new Paragraph({ children: [new PageBreak()] }),
      heading1("SECTION 5: OPTIMIZATION (Phase 3)"),

      heading2("5.1 Python Performance Optimizations"),
      bullet("Run YOLO inference in a separate thread/process to avoid blocking the PTU command loop"),
      bullet("Use a double-buffer: YOLO thread writes detection; main thread reads + sends PTU commands"),
      bullet("Use numpy for all matrix operations (already used by filterpy)"),
      bullet("Set Python process priority to high (os.nice(-10) on Linux)"),
      bullet("Use asyncio or threading.Thread for non-blocking PTU communication"),
      spacer(),

      heading2("5.2 Threading Architecture"),
      codeBlock([
        "Thread 1 (YOLO):    camera \u2192 yolo_detect \u2192 write to shared_detection (lock-free ring buffer)",
        "Thread 2 (Control): read shared_detection \u2192 kalman_update \u2192 predict \u2192 ptu_command"
      ]),
      spacer(),

      heading2("5.3 Kalman Tuning Parameters"),
      makeTable(
        ["Parameter", "Effect", "Tune When"],
        [
          ["R (measurement noise)", "Higher = trust model more", "YOLO detections are noisy/jittery"],
          ["Q (process noise)", "Higher = trust measurements more", "Drone changes direction suddenly"],
          ["dt (time step)", "Must match actual frame rate", "FPS changes"],
          ["lag_seconds", "Lookahead compensation", "Measured system lag changes"]
        ],
        [2500, 3430, 3430]
      ),
      spacer(),

      // SECTION 6
      new Paragraph({ children: [new PageBreak()] }),
      heading1("SECTION 6: TESTING & VALIDATION"),

      heading2("6.1 Test Protocol"),
      bullet("Record ground truth video with known drone trajectory (ruler-measured movement at 1 m/s)", true),
      bullet("Run new tracking code on recorded video", true),
      bullet("For each frame: log (laser_position, drone_position, on_target = distance < threshold)", true),
      bullet("Calculate success_rate = frames_on_target / total_frames", true),
      spacer(),

      heading2("6.2 Success Metrics"),
      makeTable(
        ["Test", "Pass Condition"],
        [
          ["Static drone", "100% on-target within 2 seconds"],
          ["Slow linear (0.3 m/s)", "\u226590% on-target"],
          ["Fast linear (1 m/s)", "\u226580% on-target"],
          ["Direction change", "\u22640.5s recovery time"],
          ["Detection dropout (0.5s)", "Resumes tracking after re-detection"]
        ],
        [4680, 4680]
      ),
      spacer(),

      heading2("6.3 Validation Script (pseudo-code)"),
      codeBlock([
        "results = []",
        "for frame, gt_pos in zip(video_frames, ground_truth):",
        "    detections = yolo.detect(frame)",
        "    # ... run tracker ...",
        "    laser_pos = ptu.get_current_position()",
        "    on_target = distance(laser_pos, gt_pos) < THRESHOLD_PIXELS",
        "    results.append(on_target)",
        "",
        "success_rate = sum(results) / len(results)",
        "print(f\"On-target rate: {success_rate:.1%}\")",
        "assert success_rate >= 0.80, \"Target not met -- tune Kalman parameters\""
      ]),
      spacer(),

      // SECTION 7
      new Paragraph({ children: [new PageBreak()] }),
      heading1("SECTION 7: IMPLEMENTATION TIMELINE"),

      makeTable(
        ["Week", "Phase", "Tasks"],
        [
          ["Week 1", "Phase 1: Analysis", "Instrument loop, measure latency, document interfaces"],
          ["Week 2", "Phase 2: Kalman", "Implement KalmanTracker, unit test with synthetic data"],
          ["Week 3", "Phase 2: Integration", "Integrate predictor + coordinate transform, connect to PTU"],
          ["Week 4", "Phase 3: Testing", "Run validation tests, tune parameters, achieve \u226580%"],
          ["Week 5", "Phase 3: Optimization", "Threading, performance profiling, final validation"]
        ],
        [1560, 2600, 5200]
      ),
      spacer(),

      // SECTION 8
      new Paragraph({ children: [new PageBreak()] }),
      heading1("SECTION 8: DEPENDENCIES & SETUP"),

      heading2("8.1 Python Packages"),
      codeBlock([
        "pip install filterpy numpy opencv-python ultralytics"
      ]),
      spacer(),

      heading2("8.2 Key Configuration (config.py)"),
      codeBlock([
        "# Camera",
        "FRAME_WIDTH  = 1920",
        "FRAME_HEIGHT = 1080",
        "FPS = 30",
        "",
        "# Zoom-calibrated FOV (measure for each zoom level)",
        "H_FOV_DEG = 0.5   # 36x zoom horizontal FOV",
        "V_FOV_DEG = 0.3   # 36x zoom vertical FOV",
        "",
        "# Kalman tuning",
        "KALMAN_R = 10.0",
        "KALMAN_Q = 0.1",
        "",
        "# System lag (measure in Phase 1)",
        "SYSTEM_LAG_SECONDS = 0.10",
        "",
        "# On-target threshold",
        "ON_TARGET_PIXEL_RADIUS = 20"
      ]),
      spacer(),

      // SECTION 9
      new Paragraph({ children: [new PageBreak()] }),
      heading1("SECTION 9: RISKS & MITIGATIONS"),

      makeTable(
        ["Risk", "Mitigation"],
        [
          ["FOV calibration error at 36x zoom", "Calibrate FOV per zoom level using known target distance"],
          ["Kalman diverges on fast maneuvers", "Increase Q (process noise) to track sudden acceleration"],
          ["YOLO detection gaps > 0.5s", "Implement coast mode with velocity decay"],
          ["PTU command latency spike", "Use non-blocking PTU commands; measure and compensate"],
          ["Python GIL limits throughput", "Separate YOLO to subprocess with multiprocessing.Queue"]
        ],
        [4680, 4680]
      ),
      spacer(),
      spacer(),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "END OF DOCUMENT", bold: true, font: "Arial", size: 22, color: DARK_BLUE })]
      })
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("C:\\Users\\divya\\OBJECT DETECTION\\PTU_Predictive_Tracking_Plan.docx", buffer);
  console.log("Document created successfully: PTU_Predictive_Tracking_Plan.docx");
}).catch(err => {
  console.error("Error creating document:", err);
  process.exit(1);
});
