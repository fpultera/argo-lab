{{/*
Define el nombre completo del chart.
*/}}
{{- define "mi-app-chart.fullname" -}}
{{- .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}