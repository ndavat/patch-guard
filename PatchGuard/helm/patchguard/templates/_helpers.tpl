{{-/*
Expand the name of the chart.
*/-}}
{{- define "patchguard.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{-/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS spec).
*/-}}
{{- define "patchguard.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end }}
{{- end }}
{{- end -}}

{{-/*
Common labels
*/-}}
{{- define "patchguard.labels" -}}
helm.sh/chart: {{ include "patchguard.chart" . }}
{{ include "patchguard.selectorLabels" . }}
{{- if .Values.app.kubernetes.io/managed-by }}
app.kubernetes.io/managed-by: {{ .Values.app.kubernetes.io/managed-by }}
{{- end }}
{{- end -}}

{{-/*
Selector labels
*/-}}
{{- define "patchguard.selectorLabels" -}}
app.kubernetes.io/name: {{ include "patchguard.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/part-of: {{ include "patchguard.name" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{-/*
Chart version
*/-}}
{{- define "patchguard.chart" -}}
{{- .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{- end -}}