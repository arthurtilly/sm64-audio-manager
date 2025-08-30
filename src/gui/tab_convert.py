from gui_misc import *

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import QtCore

import av

class ConvertAudioTab(MainTab):
    # Create the regular page for converting audio
    def create_page(self):
        self.audioDuration = 0
        self.sampleRate = 0
        self.numChannels = 0

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addStretch(2)

        # Line 1: Select sfx
        selectSoundFileLayout = new_widget(self.layout, QHBoxLayout)
        selectSoundFileLayout.addStretch(3)
    
        # Label
        self.selectedSoundFile = None
        self.selectedFileLabel = QLabel(text="Selected audio file: None")
        selectSoundFileLayout.addWidget(self.selectedFileLabel)

        selectSoundFileLayout.addStretch(1)
    
        # Browse button
        self.selectSoundFileButton = QPushButton(text="Browse...")
        self.selectSoundFileButton.clicked.connect(self.select_sound_file_button_pressed)
        selectSoundFileLayout.addWidget(self.selectSoundFileButton)
        self.selectSoundFileButton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        selectSoundFileLayout.addStretch(3)

        # Line 2: Input format, length, sample rate and channels
        self.inputFormatLayout = new_widget(self.layout, QHBoxLayout, spacing=5)

        self.inputLabelText = QLabel(text="Input format:")
        self.inputLabel = QLabel(text="-   ")
        self.lengthLabelText = QLabel(text="Length:")
        self.lengthLabel = QLabel(text="-   ")
        self.sampleRateLabelText = QLabel(text="Sample rate:")
        self.sampleRateLabel = QLabel(text="-   ")
        self.channelsLabelText = QLabel(text="Channels:")
        self.channelsLabel = QLabel(text="-   ")

        self.inputFormatLayout.addStretch(3)
        self.inputFormatLayout.addWidget(self.inputLabelText, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.inputFormatLayout.addWidget(self.inputLabel, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self.inputFormatLayout.addStretch(1)
        self.inputFormatLayout.addWidget(self.lengthLabelText, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.inputFormatLayout.addWidget(self.lengthLabel, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self.inputFormatLayout.addStretch(1)
        self.inputFormatLayout.addWidget(self.sampleRateLabelText, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.inputFormatLayout.addWidget(self.sampleRateLabel, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self.inputFormatLayout.addStretch(1)
        self.inputFormatLayout.addWidget(self.channelsLabelText, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.inputFormatLayout.addWidget(self.channelsLabel, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self.inputFormatLayout.addStretch(3)

        self.layout.addStretch(1)

        # Line 3: Output sample rate and mix to mono

        self.outputFormatLayout = new_widget(self.layout, QHBoxLayout)
        self.outputFormatLayout.addStretch(3)
        self.outputFormatLayout.addWidget(QLabel(text="Output sample rate:"), alignment=QtCore.Qt.AlignmentFlag.AlignRight)

        self.outputSampleRate = QLineEdit(text="")
        self.outputSampleRate.setFixedWidth(50)
        self.outputSampleRate.setValidator(QIntValidator(1, 100000))
        self.outputSampleRate.textChanged.connect(self.calculate_estimated_size)
        self.outputFormatLayout.addWidget(self.outputSampleRate)
        self.outputSampleRate.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.outputFormatLayout.addWidget(QLabel(text="Hz"), alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self.outputFormatLayout.addStretch(1)

        self.monoCheckbox = QCheckBox(text="Mix down to mono?")
        self.outputFormatLayout.addWidget(self.monoCheckbox)
        self.monoCheckbox.stateChanged.connect(self.calculate_estimated_size)
        fix_checkbox_palette(self.monoCheckbox)

        self.outputFormatLayout.addStretch(3)

        # Line 4: Output path
        self.outputPathLayout = new_widget(self.layout, QHBoxLayout)
        self.outputPathLayout.addStretch(1)

        self.outputPathLayout.addWidget(QLabel(text="Output path:"), alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.outputPath = QLineEdit(text="")
        self.outputPath.setFixedWidth(300)
        self.outputPathLayout.addWidget(self.outputPath, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

        self.outputBrowseButton = QPushButton(text="Browse...")
        self.outputPathLayout.addWidget(self.outputBrowseButton)
        self.outputBrowseButton.clicked.connect(self.output_browse_button_pressed)
        self.outputBrowseButton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.outputPathLayout.addStretch(1)

        # Line 5: Estimated ROM size
        self.estimatedSizeLabel = QLabel(text="Estimated size in ROM: -")
        self.estimatedSizeLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.estimatedSizeLabel)

        self.layout.addStretch(1)

        # Convert button
        convertWidget, self.convertButton = add_centered_button_to_layout(self.layout, "Convert!", self.convert_pressed)

        # Import info
        self.infoLabel = QLabel(text="")
        self.infoLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.infoLabel)

        self.layout.addStretch(2)

        self.toggleableWidgets = (
            self.inputFormatLayout.parentWidget(),
            self.outputFormatLayout.parentWidget(),
            self.outputPathLayout.parentWidget(),
            self.estimatedSizeLabel,
            convertWidget
        )

        self.toggle_import_options(False)

    
    def toggle_import_options(self, enabled):
        for widget in self.toggleableWidgets:
            widget.setEnabled(enabled)

    # Calculate the estimated size of the imported audio
    def calculate_estimated_size(self):
        try:
            sampleRate = int(self.outputSampleRate.text())
        except ValueError:
            return
        numChannels = 1 if self.monoCheckbox.isChecked() else self.numChannels
        estBytes = self.audioDuration * sampleRate * numChannels * (9 / 16)
        estMB = estBytes / 1048576

        if estMB < 1:
            self.estimatedSizeLabel.setText("Estimated size in ROM: %.2f KB" % (estBytes / 1024))
        else:
            self.estimatedSizeLabel.setText("Estimated size in ROM: %.2f MB" % estMB)


    # Browsing for input audio file
    def select_sound_file_button_pressed(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        # Accept any audio file
        dialog.setNameFilter("Audio files (*.wav *.mp3 *.ogg *.flac *.aiff *.aif *.aifc)")
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            self.inputFile = dialog.selectedFiles()[0]

            # Attempt to open audio file
            try:
                inputStream = av.open(self.inputFile)
            except av.AVError:
                # Invalid file
                self.selectedFileLabel.setText("Selected audio file: None")
                self.inputLabel.setText("-   ")
                self.lengthLabel.setText("-   ")
                self.sampleRateLabel.setText("-   ")
                self.channelsLabel.setText("-   ")
                self.outputSampleRate.setText("")
                self.estimatedSizeLabel.setText("Estimated size in ROM: -")
                self.outputPath.setText("")
                self.toggle_import_options(False)
                self.set_info_message("Error: Invalid audio file", COLOR_RED)
                return
            self.clear_info_message()

            # Set labels based on audio file properties
            self.selectedFileLabel.setText("Selected audio file: " + os.path.basename(self.inputFile))
            self.inputLabel.setText(inputStream.format.name.upper())
            
            duration = inputStream.duration / 1000000
            self.audioDuration = duration
            durationStr = ""
            if duration > 60:
                durationStr += "%dm " % int(duration / 60)
                duration -= int(duration / 60) * 60
            durationStr += "%.1fs" % duration
            self.lengthLabel.setText(durationStr)

            self.sampleRate = inputStream.streams.audio[0].codec_context.sample_rate
            self.sampleRateLabel.setText("%dHz" % self.sampleRate)
            self.outputSampleRate.setText("%d" % self.sampleRate)

            self.numChannels = inputStream.streams.audio[0].codec_context.channels
            self.channelsLabel.setText("%d" % self.numChannels)

            inputStream.close()

            # Determine default output path and estimated size
            curDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
            baseName = os.path.splitext(os.path.basename(self.inputFile))[0]
            self.outputPath.setText(os.path.join(curDir, "export", baseName + ".aiff"))
            self.calculate_estimated_size()

            self.toggle_import_options(True)


    # Browsing for output path
    def output_browse_button_pressed(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        dialog.setNameFilter("AIFF files (*.aiff)")
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        if os.path.isdir(os.path.dirname(self.outputPath.text())):
            # Auto navigate to directory
            dialog.setDirectory(os.path.dirname(self.outputPath.text()))
        # Set file name
        dialog.selectFile(os.path.basename(self.outputPath.text()))
        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            self.outputPath.setText(dialog.selectedFiles()[0])


    # Convert audio
    def convert_pressed(self):
        # Check if output path is valid
        if not os.path.isdir(os.path.dirname(self.outputPath.text())):
            os.makedirs(os.path.dirname(self.outputPath.text()))
        
        inputFile = av.open(self.inputFile)
        outputFile = av.open(self.outputPath.text(), mode="w")

        outputSampleRate = int(self.outputSampleRate.text())

        in_stream = inputFile.streams.audio[0]
        out_stream = outputFile.add_stream("pcm_s16be", outputSampleRate)
        out_stream.channels = 1 if self.monoCheckbox.isChecked() else in_stream.channels

        # Resample audio
        resampler = av.AudioResampler(
            format="s16",
            layout="mono" if self.monoCheckbox.isChecked() else in_stream.layout.name,
            rate=outputSampleRate
        )

        for packet in inputFile.demux(in_stream):
            try:
                for frame in packet.decode():
                    newFrames = resampler.resample(frame)
                    for frame in newFrames:
                        for packet in out_stream.encode(frame):
                            outputFile.mux(packet)
            except av.AVError:
                continue

        inputFile.close()
        outputFile.close()

        self.mainWindow.set_all_audio_files(self.outputPath.text())
        self.set_info_message("Success!", COLOR_GREEN)
