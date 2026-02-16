"""Similarity analyzer widget for Qt6 GUI."""

from pathlib import Path
from typing import Optional, List

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTextEdit,
    QGroupBox,
    QMessageBox,
    QProgressBar,
    QSpinBox,
    QCheckBox,
)

from bpui.utils.file_io.pack_io import list_drafts
from bpui.features.similarity.engine import SimilarityAnalyzer, format_similarity_report
from bpui.core.config import Config


class SimilarityWidget(QWidget):
    """Character similarity analyzer widget."""
    
    def __init__(self, main_window):
        """Initialize similarity widget.
        
        Args:
            main_window: Reference to main window for navigation
        """
        super().__init__()
        self.main_window = main_window
        
        self.analyzer = SimilarityAnalyzer()
        self.drafts_root = Path.cwd() / "drafts"
        self.draft_list = []
        self.draft_paths = {}
        
        self._setup_ui()
        self._load_drafts()
    
    def _setup_ui(self) -> None:
        """Setup user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        title = QLabel("🔍 Character Similarity Analyzer")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Description
        description = QLabel(
            "Compare two characters to find commonalities, differences, "
            "and assess relationship potential."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Character selection group
        selection_group = QGroupBox("Select Characters")
        selection_layout = QVBoxLayout()
        selection_group.setLayout(selection_layout)
        
        # Character 1
        char1_label = QLabel("First Character:")
        selection_layout.addWidget(char1_label)
        
        self.char1_combo = QComboBox()
        self.char1_combo.setMinimumWidth(300)
        selection_layout.addWidget(self.char1_combo)
        
        # Character 2
        char2_label = QLabel("Second Character:")
        selection_layout.addWidget(char2_label)
        
        self.char2_combo = QComboBox()
        self.char2_combo.setMinimumWidth(300)
        selection_layout.addWidget(self.char2_combo)
        
        layout.addWidget(selection_group)
        
        # Compare button
        self.compare_btn = QPushButton("🔍 Compare Characters")
        self.compare_btn.setMinimumHeight(40)
        self.compare_btn.clicked.connect(self._on_compare_clicked)
        layout.addWidget(self.compare_btn)
        
        # LLM Analysis option
        llm_group = QGroupBox("LLM Analysis")
        llm_layout = QVBoxLayout()
        llm_group.setLayout(llm_layout)
        
        self.use_llm_checkbox = QCheckBox("Enable LLM Deep Analysis")
        self.use_llm_checkbox.setToolTip(
            "Use LLM for deeper character relationship analysis "
            "(requires LLM engine configured)"
        )
        llm_layout.addWidget(self.use_llm_checkbox)
        
        layout.addWidget(llm_group)
        
        # Batch options
        batch_group = QGroupBox("Batch Analysis")
        batch_layout = QVBoxLayout()
        batch_group.setLayout(batch_layout)
        
        # Compare all checkbox
        self.compare_all_checkbox = QCheckBox("Compare All Pairs")
        self.compare_all_checkbox.setToolTip(
            "Compare all pairs of characters in drafts directory"
        )
        batch_layout.addWidget(self.compare_all_checkbox)
        
        # Cluster checkbox
        self.cluster_checkbox = QCheckBox("Cluster Similar Characters")
        self.cluster_checkbox.setToolTip(
            "Group similar characters together"
        )
        batch_layout.addWidget(self.cluster_checkbox)
        
        # Threshold spinbox
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Similarity Threshold:")
        threshold_layout.addWidget(threshold_label)
        
        self.threshold_spinbox = QSpinBox()
        self.threshold_spinbox.setRange(0, 100)
        self.threshold_spinbox.setValue(60)
        self.threshold_spinbox.setSuffix("%")
        threshold_layout.addWidget(self.threshold_spinbox)
        
        batch_layout.addLayout(threshold_layout)
        
        layout.addWidget(batch_group)
        
        # Results area
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        results_group.setLayout(results_layout)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMinimumHeight(400)
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        # Back button
        back_btn = QPushButton("← Back")
        back_btn.setMinimumHeight(30)
        back_btn.clicked.connect(lambda: self.main_window.show_home())
        layout.addWidget(back_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
    
    def _load_drafts(self) -> None:
        """Load list of available drafts."""
        try:
            draft_paths = list_drafts(self.drafts_root)
            
            # Sort by name
            draft_paths = sorted(draft_paths, key=lambda x: x.name)
            
            # Clear and populate combos
            self.char1_combo.clear()
            self.char2_combo.clear()
            self.draft_paths.clear()
            
            for draft_path in draft_paths:
                self.char1_combo.addItem(draft_path.name)
                self.char2_combo.addItem(draft_path.name)
                self.draft_paths[draft_path.name] = draft_path
            
            self.results_text.setText(
                f"Loaded {len(draft_paths)} characters. "
                "Select two characters to compare."
            )
        
        except Exception as e:
            self.results_text.setText(f"Error loading drafts: {e}")
    
    def _on_compare_clicked(self) -> None:
        """Handle compare button click."""
        # Check batch options
        if self.compare_all_checkbox.isChecked():
            self._compare_all_pairs()
        elif self.cluster_checkbox.isChecked():
            self._cluster_characters()
        else:
            self._compare_pair()
    
    def _compare_pair(self) -> None:
        """Compare selected pair of characters."""
        # Get selections
        char1_name = self.char1_combo.currentText()
        char2_name = self.char2_combo.currentText()
        
        if not char1_name or not char2_name:
            QMessageBox.warning(
                self, "Selection Required",
                "Please select two characters to compare."
            )
            return
        
        if char1_name == char2_name:
            QMessageBox.warning(
                self, "Invalid Selection",
                "Please select different characters."
            )
            return
        
        # Get paths
        draft1 = self.draft_paths.get(char1_name)
        draft2 = self.draft_paths.get(char2_name)
        
        if not draft1 or not draft2:
            QMessageBox.critical(
                self, "Error",
                "Could not find selected character drafts."
            )
            return
        
        # Check if LLM analysis is requested
        use_llm = self.use_llm_checkbox.isChecked()
        llm_engine = None
        
        if use_llm:
            from bpui.llm.factory import create_engine

            try:
                config = Config()

                # Create engine using factory
                engine = create_engine(
                    config,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )

                llm_engine = engine
                self.results_text.setText("Comparing characters with LLM analysis...")
            except (ImportError, ValueError, RuntimeError) as e:
                QMessageBox.warning(
                    self, "LLM Error",
                    f"Could not initialize LLM engine: {e}\n"
                    "Proceeding with basic analysis only."
                )
                use_llm = False
        else:
            self.results_text.setText("Comparing characters...")
        
        # Perform comparison
        self.compare_btn.setEnabled(False)
        
        try:
            result = self.analyzer.compare_drafts(draft1, draft2, use_llm=use_llm, llm_engine=llm_engine)
            
            if result:
                report = format_similarity_report(result)
                self.results_text.setText(report)
            else:
                self.results_text.setText("Failed to compare characters.")
        
        except Exception as e:
            self.results_text.setText(f"Error: {e}")
            QMessageBox.critical(
                self, "Error",
                f"Failed to compare characters: {e}"
            )
        
        finally:
            self.compare_btn.setEnabled(True)
    
    def _compare_all_pairs(self) -> None:
        """Compare all pairs of characters."""
        # Get all draft paths
        draft_dirs = []
        if self.drafts_root.exists():
            for item in self.drafts_root.iterdir():
                if item.is_dir() and (item / "character_sheet.txt").exists():
                    draft_dirs.append(item)
        
        if not draft_dirs:
            QMessageBox.warning(
                self, "No Drafts",
                "No character drafts found in the drafts directory."
            )
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.results_text.setText("Comparing all character pairs...")
        self.compare_btn.setEnabled(False)
        
        try:
            # Perform comparison
            results = self.analyzer.compare_multiple(draft_dirs)
            
            # Sort by overall similarity
            sorted_results = sorted(
                results.items(),
                key=lambda x: x[1].overall_score,
                reverse=True
            )
            
            # Build report
            lines = []
            lines.append(f"📊 Analyzed {len(results)} pairs\n")
            lines.append("=" * 60)
            
            for (char1, char2), result in sorted_results:
                lines.append(f"\n{char1} vs {char2}")
                lines.append(f"Similarity: {result.overall_score * 100:.1f}%")
                lines.append(f"Compatibility: {result.compatibility.upper()}")
                lines.append("-" * 40)
            
            self.results_text.setText('\n'.join(lines))
            self.progress_bar.setValue(100)
        
        except Exception as e:
            self.results_text.setText(f"Error: {e}")
            QMessageBox.critical(
                self, "Error",
                f"Failed to compare characters: {e}"
            )
        
        finally:
            self.compare_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def _cluster_characters(self) -> None:
        """Cluster similar characters."""
        # Get all draft paths
        draft_dirs = []
        if self.drafts_root.exists():
            for item in self.drafts_root.iterdir():
                if item.is_dir() and (item / "character_sheet.txt").exists():
                    draft_dirs.append(item)
        
        if not draft_dirs:
            QMessageBox.warning(
                self, "No Drafts",
                "No character drafts found in the drafts directory."
            )
            return
        
        # Get threshold
        threshold = self.threshold_spinbox.value() / 100.0
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.results_text.setText(f"Clustering characters ({threshold:.0%} threshold)...")
        self.compare_btn.setEnabled(False)
        
        try:
            # Perform clustering
            clusters = self.analyzer.cluster_characters(
                draft_dirs,
                min_similarity=threshold
            )
            
            # Build report
            lines = []
            lines.append(f"📦 Found {len(clusters)} clusters:\n")
            lines.append("=" * 60)
            
            for i, cluster in enumerate(clusters, 1):
                lines.append(f"\nCluster {i} ({len(cluster)} characters):")
                for char_name in cluster:
                    lines.append(f"  • {char_name}")
            
            self.results_text.setText('\n'.join(lines))
            self.progress_bar.setValue(100)
        
        except Exception as e:
            self.results_text.setText(f"Error: {e}")
            QMessageBox.critical(
                self, "Error",
                f"Failed to cluster characters: {e}"
            )
        
        finally:
            self.compare_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    @Slot()
    def refresh(self) -> None:
        """Refresh draft list."""
        self._load_drafts()