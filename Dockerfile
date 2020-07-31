FROM python:3.8
 WORKDIR /home/box_mcas 
ENV PYTHONPATH "${PYTHONPATH}:/home/box_mcas" 
COPY . .
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
      curl https://packages.microsoft.com/config/debian/9/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
      apt-get update && \
      ACCEPT_EULA=Y apt-get install msodbcsql17 unixodbc-dev -y && \
      groupadd docker && \
      useradd -m -g docker docker && \
      touch /home/box_mcas/logs/box-mcas.info.log && \
      touch /home/box_mcas/logs/box-mcas.error.log && \
      chown -R docker:docker /home/box_mcas && \
      python -m pip install --upgrade pip && \
      pip install -r requirements.txt 
USER docker 
CMD ["python", "src/main.py", "mcas-policy-box-classification-sync", "-e", "prod"] 