# scorecard:stable sept 17, 2021
FROM gcr.io/openssf/scorecard@sha256:d133044202e76a2f72a18f96c6de559110c829e97002cd77a4ca87448b4e997a AS scorecard

FROM golang@sha256:3c4de86eec9cbc619cdd72424abd88326ffcf5d813a8338a7743c55e5898734f
# Install python3 and copy the scripts
RUN apt-get update
RUN apt-get -y install python3
RUN apt-get -y install python3-pip
RUN pip3 install tqdm
ADD scorecard.py /bin/

# Compile and install the vanity resolver
ADD ./go-vanity-resolver /src
WORKDIR /src
RUN CGO_ENABLED=0 go build -o go-vanity-resolver
RUN mv go-vanity-resolver /bin/

# Copy the scorecard binary from the existing image
COPY --from=scorecard /scorecard /bin/

WORKDIR /
CMD ["/bin/bash"]
