{{/*
Chart name.
*/}}
{{- define "portfolio-frontend.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common Kubernetes labels.
*/}}
{{- define "portfolio-frontend.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "portfolio-frontend.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Application selector labels.
*/}}
{{- define "portfolio-frontend.selectorLabels" -}}
app.kubernetes.io/name: {{ include "portfolio-frontend.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
