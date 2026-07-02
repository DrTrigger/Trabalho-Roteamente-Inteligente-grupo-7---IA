import reflex as rx

config = rx.Config(
    app_name="projeto_ia_roteamento",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)