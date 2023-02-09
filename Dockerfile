# start by pulling the python image
FROM python:3.8

# copy the requirements file into the image
COPY ./requirements.txt /app/requirements.txt

# switch working directory
WORKDIR /app

# install the dependencies and packages in the requirements file
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install pandas
RUN python3 -m pip install numpy
RUN python3 -m pip install -r requirements.txt

# copy every content from the local file to the image
COPY . /app

# configure the container to run in an executed manner

CMD ["python3", "LeverageModelling.py" ]