"""Lineage tree viewer for GUI."""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTreeWidget, QTreeWidgetItem, QComboBox, QSpinBox,
    QTextEdit, QSplitter, QGroupBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class LineageWidget(QWidget):
    """Widget for displaying character lineage trees."""

    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.drafts_dir = Path.cwd() / "drafts"
        self.tree_data = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()

        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(self.back_requested.emit)
        header.addWidget(back_btn)

        title = QLabel("Character Lineage")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header.addWidget(title)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_tree)
        header.addWidget(refresh_btn)

        header.addStretch()
        layout.addLayout(header)

        # Options panel
        options_group = QGroupBox("Display Options")
        options_layout = QHBoxLayout()

        # Generation filter
        options_layout.addWidget(QLabel("Generation:"))
        self.gen_filter = QComboBox()
        self.gen_filter.addItem("All", None)
        self.gen_filter.currentIndexChanged.connect(self.filter_changed)
        options_layout.addWidget(self.gen_filter)

        # Max depth
        options_layout.addWidget(QLabel("Max Depth:"))
        self.max_depth = QSpinBox()
        self.max_depth.setMinimum(1)
        self.max_depth.setMaximum(10)
        self.max_depth.setValue(10)
        self.max_depth.valueChanged.connect(self.filter_changed)
        options_layout.addWidget(self.max_depth)

        # Filters
        self.roots_only = QCheckBox("Roots Only")
        self.roots_only.stateChanged.connect(self.filter_changed)
        options_layout.addWidget(self.roots_only)

        self.leaves_only = QCheckBox("Leaves Only")
        self.leaves_only.stateChanged.connect(self.filter_changed)
        options_layout.addWidget(self.leaves_only)

        options_layout.addStretch()
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Main content - splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Tree view
        tree_group = QGroupBox("Family Tree")
        tree_layout = QVBoxLayout()

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Character", "Generation", "Offspring Type", "Children"])
        self.tree_widget.currentItemChanged.connect(self.on_selection_changed)
        tree_layout.addWidget(self.tree_widget)

        tree_group.setLayout(tree_layout)
        splitter.addWidget(tree_group)

        # Details panel
        details_group = QGroupBox("Character Details")
        details_layout = QVBoxLayout()

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)

        # Actions
        actions_layout = QHBoxLayout()

        self.view_draft_btn = QPushButton("View Draft")
        self.view_draft_btn.setEnabled(False)
        self.view_draft_btn.clicked.connect(self.view_selected_draft)
        actions_layout.addWidget(self.view_draft_btn)

        self.compare_parents_btn = QPushButton("Compare Parents")
        self.compare_parents_btn.setEnabled(False)
        self.compare_parents_btn.clicked.connect(self.compare_parents)
        actions_layout.addWidget(self.compare_parents_btn)

        actions_layout.addStretch()
        details_layout.addLayout(actions_layout)

        details_group.setLayout(details_layout)
        splitter.addWidget(details_group)

        splitter.setSizes([800, 600])
        layout.addWidget(splitter)

        # Statistics footer
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)

    def load_tree(self):
        """Load and display the lineage tree."""
        from bpui.utils.lineage import LineageTree

        if not self.drafts_dir.exists():
            self.stats_label.setText(f"❌ Drafts directory not found: {self.drafts_dir}")
            return

        # Build tree
        self.tree_data = LineageTree(self.drafts_dir)

        # Update generation filter
        self.gen_filter.clear()
        self.gen_filter.addItem("All", None)
        for gen in range(self.tree_data.get_max_generation() + 1):
            self.gen_filter.addItem(f"Generation {gen}", gen)

        # Display tree
        self.display_tree()

        # Update stats
        stats = []
        stats.append(f"Total: {len(self.tree_data.nodes)}")
        stats.append(f"Roots: {len(self.tree_data.roots)}")
        stats.append(f"Generations: {self.tree_data.get_max_generation() + 1}")
        stats.append(f"Leaves: {len(self.tree_data.get_leaves())}")
        self.stats_label.setText(" | ".join(stats))

    def display_tree(self):
        """Display the tree in the widget."""
        self.tree_widget.clear()

        if not self.tree_data or not self.tree_data.roots:
            self.tree_widget.addTopLevelItem(QTreeWidgetItem(["No characters found"]))
            return

        # Apply filters
        nodes_to_display = self.get_filtered_nodes()

        # If filtering by generation, show flat list
        if self.gen_filter.currentData() is not None:
            for node in nodes_to_display:
                item = self.create_tree_item(node)
                self.tree_widget.addTopLevelItem(item)
        # Otherwise show hierarchy
        else:
            for root in self.tree_data.roots:
                if root in nodes_to_display:
                    root_item = self.create_tree_item(root, include_children=True)
                    self.tree_widget.addTopLevelItem(root_item)

        self.tree_widget.expandAll()

    def get_filtered_nodes(self):
        """Get nodes matching current filters."""
        nodes = list(self.tree_data.nodes.values())

        # Filter by generation
        if self.gen_filter.currentData() is not None:
            gen = self.gen_filter.currentData()
            nodes = [n for n in nodes if n.generation == gen]

        # Filter roots/leaves
        if self.roots_only.isChecked():
            nodes = [n for n in nodes if n.is_root]
        elif self.leaves_only.isChecked():
            nodes = [n for n in nodes if n.is_leaf]

        return nodes

    def create_tree_item(self, node, include_children=False, depth=0):
        """Create a tree widget item for a node."""
        # Node info
        char_name = node.character_name
        gen = str(node.generation)
        offspring_type = node.offspring_type or "-"
        num_children = str(len(node.children))

        item = QTreeWidgetItem([char_name, gen, offspring_type, num_children])
        item.setData(0, Qt.ItemDataRole.UserRole, node)  # Store node reference

        # Add children recursively
        if include_children and depth < self.max_depth.value():
            for child in node.children:
                child_item = self.create_tree_item(child, include_children=True, depth=depth+1)
                item.addChild(child_item)

        return item

    def on_selection_changed(self, current, previous):
        """Handle selection change in tree."""
        if not current:
            self.details_text.clear()
            self.view_draft_btn.setEnabled(False)
            self.compare_parents_btn.setEnabled(False)
            return

        node = current.data(0, Qt.ItemDataRole.UserRole)
        if not node:
            return

        # Get family summary
        summary = self.tree_data.get_family_summary(node)

        # Build details text
        details = []
        details.append(f"<h2>{summary['character_name']}</h2>")
        details.append(f"<b>Generation:</b> {summary['generation']}")
        details.append(f"<b>Draft Path:</b> {node.draft_path.name}")

        if summary['offspring_type']:
            details.append(f"<b>Offspring Type:</b> {summary['offspring_type']}")

        if node.metadata.mode:
            details.append(f"<b>Mode:</b> {node.metadata.mode}")

        if node.metadata.model:
            details.append(f"<b>Model:</b> {node.metadata.model}")

        if node.metadata.created:
            created = node.metadata.created[:19] if len(node.metadata.created) > 19 else node.metadata.created
            details.append(f"<b>Created:</b> {created}")

        details.append("<hr>")

        # Family relationships
        details.append(f"<h3>Family Relationships</h3>")

        if summary['parent_names']:
            parents = ", ".join(summary['parent_names'])
            details.append(f"<b>Parents:</b> {parents}")
        else:
            details.append(f"<b>Parents:</b> None (root character)")

        if summary['children_names']:
            children = ", ".join(summary['children_names'])
            details.append(f"<b>Children:</b> {children}")
        else:
            details.append(f"<b>Children:</b> None (leaf character)")

        if summary['sibling_names']:
            siblings = ", ".join(summary['sibling_names'])
            details.append(f"<b>Siblings:</b> {siblings}")

        details.append("<hr>")

        # Statistics
        details.append(f"<h3>Statistics</h3>")
        details.append(f"<b>Total Ancestors:</b> {summary['num_ancestors']}")
        details.append(f"<b>Total Descendants:</b> {summary['num_descendants']}")

        # Lineage paths
        if summary['num_ancestors'] > 0:
            details.append("<hr>")
            details.append(f"<h3>Lineage Paths</h3>")
            paths = self.tree_data.get_lineage_path(node)
            for i, path in enumerate(paths, 1):
                path_str = " → ".join(n.character_name for n in path)
                details.append(f"<b>Path {i}:</b> {path_str}")

        self.details_text.setHtml("<br>".join(details))

        # Enable actions
        self.view_draft_btn.setEnabled(True)
        self.compare_parents_btn.setEnabled(len(summary['parent_names']) > 0)

    def filter_changed(self):
        """Handle filter change."""
        # Prevent roots and leaves being checked together
        if self.roots_only.isChecked() and self.leaves_only.isChecked():
            sender = self.sender()
            if sender == self.roots_only:
                self.leaves_only.setChecked(False)
            else:
                self.roots_only.setChecked(False)

        self.display_tree()

    def view_selected_draft(self):
        """View the selected draft in review screen."""
        current = self.tree_widget.currentItem()
        if not current:
            return

        node = current.data(0, Qt.ItemDataRole.UserRole)
        if not node:
            return

        # Load draft assets
        from bpui.utils.file_io.pack_io import load_draft

        try:
            assets = load_draft(node.draft_path)
            # Navigate to review screen
            main_window = self.window()
            if hasattr(main_window, 'show_review'):
                main_window.show_review(node.draft_path, assets)
        except Exception as e:
            self.stats_label.setText(f"❌ Failed to load draft: {e}")

    def compare_parents(self):
        """Compare parent characters using similarity screen."""
        current = self.tree_widget.currentItem()
        if not current:
            return

        node = current.data(0, Qt.ItemDataRole.UserRole)
        if not node or not node.parents:
            return

        if len(node.parents) < 2:
            self.stats_label.setText("❌ Need at least 2 parents to compare")
            return

        # Navigate to similarity screen
        main_window = self.window()
        if hasattr(main_window, 'show_similarity'):
            # Just navigate to similarity screen - user can select parents manually
            main_window.show_similarity()
            self.stats_label.setText(f"📊 Navigate to Similarity screen to compare {node.parents[0].character_name} and {node.parents[1].character_name}")

    def refresh(self):
        """Refresh the lineage tree."""
        self.load_tree()
