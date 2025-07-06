import customtkinter as ctk
from ui.home_view import HomeView
from ui.guide_view import GuideView
from ui.yt_view import YtView
from utils import app_config


class AppFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")

        # --- Top Navigation ---
        self.top_nav_frame = ctk.CTkFrame(self, height=0, corner_radius=0, fg_color='transparent')
        self.top_nav_frame.pack(fill="x", side="top")
        
        self.app_title_label = ctk.CTkLabel(
            self.top_nav_frame,
            text=app_config.APP_NAME,
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.app_title_label.pack(side="left", padx=5, pady=(5,20))

        # --- Custom Tab Buttons ---
        self.create_custom_tabs()

        # --- Content Area ---
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.pack(fill="both", expand=True)

        # Initialize content views
        self.home_view = HomeView(self.content_container)
        self.yt_view = YtView(self.content_container)
        self.guide_view = GuideView(self.content_container)

        # Initially show home view
        self.currentTab = ""
        self.show_content(app_config.TAB_HOME)
        

    def create_custom_tabs(self):
        """
        Creates custom tab buttons centered horizontally beneath title label,
        equally spaced across container width.
        """
        self.tab_buttons_frame = ctk.CTkFrame(
            self,
            fg_color='transparent',
        )
        self.tab_buttons_frame.pack(fill="x", side="top")

        num_tabs = len([app_config.TAB_HOME, app_config.TAB_YT, app_config.TAB_GUIDE])
        for idx in range(num_tabs):
            self.tab_buttons_frame.grid_columnconfigure(idx, weight=1)

        ButtonTitles = [
                app_config.TAB_HOME,
                app_config.TAB_YT,
                app_config.TAB_GUIDE
            ]

        self.buttons = []  # For potential later manipulation

        for col_idx, tab_title in enumerate(ButtonTitles):
            btn = ctk.CTkButton(
                self.tab_buttons_frame,
                text=tab_title,
                corner_radius=1,
                height=26,
                #fg_color="transparent",
                #text_color=("black", "gray"),
                hover_color=("#4A4C72"),
                command=lambda title=tab_title: self.show_content(title),
            )
            btn.grid(row=0, column=col_idx, sticky="ew", padx=0)
            self.buttons.append(btn)

    def show_content(self, tab_name):
        """
        Shows selected tab content and hides others.
        Can be extended later with visual active tab indicators/styles.
        """

        if self.currentTab == tab_name: 
            return


        self.highlight_active_tab(tab_name)

        # Hide all content views
        self.home_view.pack_forget()
        self.yt_view.pack_forget()
        self.guide_view.pack_forget()

        # Show requested view
        if tab_name == app_config.TAB_HOME:
            self.home_view.pack(fill="both", expand=True, padx=0, pady=(10,0))
        elif tab_name == app_config.TAB_YT:
            self.yt_view.pack(fill="both", expand=True, padx=0, pady=(10,0))
        elif tab_name == app_config.TAB_GUIDE:
            self.guide_view.pack(fill="both", expand=True, padx=0, pady=(10, 0))

        self.currentTab = tab_name


    def highlight_active_tab(self, tab_name):
        """
        Highlights the selected tab button and resets others back to default styling.
        """
        ButtonTitles = [app_config.TAB_HOME, app_config.TAB_YT, app_config.TAB_GUIDE]

        for btn in self.buttons:
            btn.configure(fg_color="#414141")

        idx = ButtonTitles.index(tab_name)
        self.buttons[idx].configure(fg_color="#4A4C72")