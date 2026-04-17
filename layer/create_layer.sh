

# 2. Create the required 'python' folder
mkdir python

# 3. Install Pillow and Requests together (Forces clean Linux binaries)
pip install --platform manylinux2014_x86_64 --target=python --implementation cp --python-version 3.14 --only-binary= :all: --upgrade Pillow requests

# 4. Zip it up
# Compress-Archive -Path python -DestinationPath combined_layer.zip

# 5 For Linux
zip -r combined_layer.zip python