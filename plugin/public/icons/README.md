# Icons

Pour générer les icônes PNG depuis le SVG, utilisez:

```bash
# Installer imagemagick si nécessaire
sudo apt install imagemagick

# Générer les icônes
convert icon.svg -resize 16x16 icon16.png
convert icon.svg -resize 48x48 icon48.png
convert icon.svg -resize 128x128 icon128.png
```

Ou créez-les manuellement dans un éditeur d'images.
