# Run this command to generate the Amazon Linux compatible Pillow layer
mkdir python
pip install --platform manylinux2014_x86_64 --target=python --implementation cp --python-version 3.12 --only-binary=:all: --upgrade Pillow
zip -r pillow_layer.zip python/