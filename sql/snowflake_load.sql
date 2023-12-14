"COPY INTO organizations (Index,Organization_Id,Name,Website,Country,Description,Founded,Industry,Number_of_employees)
FROM @my_s3_stage
FILE_FORMAT = (FORMAT_NAME = my_csv_format)
ON_ERROR=CONTINUE"