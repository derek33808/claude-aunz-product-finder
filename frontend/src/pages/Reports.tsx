import { useState, useEffect } from 'react';
import { Card, Button, Table, Tag, Space, Modal, Form, Input, Select, Progress, message, Descriptions, Row, Col } from 'antd';
import { PlusOutlined, ReloadOutlined, DownloadOutlined, ShareAltOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { useTranslation } from 'react-i18next';
import { reportsApi } from '../services/api';
import type { Report, ReportCreate } from '../types';

const { Option } = Select;

const Reports = () => {
  const { t } = useTranslation();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(false);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [viewReport, setViewReport] = useState<Report | null>(null);
  const [generating, setGenerating] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => { loadReports(); }, []);

  const loadReports = async () => {
    setLoading(true);
    try {
      const data = await reportsApi.list();
      setReports(data);
    } catch (error) { message.error(t('reports.generateFailed')); }
    finally { setLoading(false); }
  };

  const handleCreateReport = async (values: any) => {
    setGenerating(true);
    try {
      const reportData: ReportCreate = {
        title: values.title,
        report_type: values.report_type,
        target_type: values.target_type,
        target_value: values.target_value,
      };
      await reportsApi.generate(reportData);
      message.success(t('reports.generating'));
      setCreateModalOpen(false);
      form.resetFields();
      setTimeout(loadReports, 2000);
    } catch (error) { message.error(t('reports.generateFailed')); }
    finally { setGenerating(false); }
  };

  const handleDelete = async (id: string) => {
    try {
      await reportsApi.delete(id);
      message.success(t('common.success'));
      loadReports();
    } catch (error) { message.error(t('reports.deleteFailed')); }
  };

  const getScoreChartOption = (report: Report) => {
    return {
      series: [{
        type: 'gauge',
        startAngle: 180,
        endAngle: 0,
        min: 0,
        max: 100,
        pointer: { show: false },
        progress: { show: true, width: 18 },
        axisLine: { lineStyle: { width: 18 } },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        detail: { valueAnimation: true, fontSize: 30, offsetCenter: [0, '-20%'] },
        data: [{ value: report.overall_score || 0 }]
      }]
    };
  };

  const columns = [
    { title: t('reports.reportTitle'), dataIndex: 'title', key: 'title', ellipsis: true },
    { title: t('reports.type'), dataIndex: 'report_type', key: 'type', render: (type: string) => <Tag>{type.toUpperCase()}</Tag> },
    { title: t('reports.status'), dataIndex: 'status', key: 'status', render: (s: string, r: Report) => (
      <Space>
        <Tag color={s === 'completed' ? 'green' : s === 'generating' ? 'blue' : s === 'failed' ? 'red' : 'default'}>{s}</Tag>
        {s === 'generating' && <Progress percent={r.progress} size="small" style={{ width: 100 }} />}
      </Space>
    )},
    { title: t('reports.score'), dataIndex: 'overall_score', key: 'score', render: (s: number) => s ? <Tag color={s >= 70 ? 'green' : s >= 40 ? 'orange' : 'red'}>{s}/100</Tag> : '-' },
    { title: t('reports.created'), dataIndex: 'created_at', key: 'created', render: (d: string) => new Date(d).toLocaleDateString() },
    { title: t('reports.actions'), key: 'actions', render: (_: any, record: Report) => (
      <Space>
        <Button size="small" icon={<EyeOutlined />} onClick={() => setViewReport(record)} disabled={record.status !== 'completed'} title={t('reports.view')} />
        <Button size="small" icon={<DownloadOutlined />} disabled={!record.pdf_path} title={t('reports.download')} />
        <Button size="small" icon={<ShareAltOutlined />} disabled={record.status !== 'completed'} />
        <Button size="small" icon={<DeleteOutlined />} danger onClick={() => handleDelete(record.id)} title={t('reports.delete')} />
      </Space>
    )},
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>{t('reports.title')}</h1>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadReports} loading={loading}>{t('dashboard.refresh')}</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>{t('reports.generateNew')}</Button>
        </Space>
      </div>

      <Card>
        <Table dataSource={reports} columns={columns} rowKey="id" loading={loading} pagination={{ pageSize: 10 }}
          locale={{ emptyText: t('reports.noReports') }} />
      </Card>

      {/* Create Report Modal */}
      <Modal title={t('reports.generateNew')} open={createModalOpen} onCancel={() => setCreateModalOpen(false)} footer={null} width={500}>
        <Form form={form} layout="vertical" onFinish={handleCreateReport}>
          <Form.Item name="title" label={t('reports.reportTitle')}><Input placeholder={t('reports.reportTitlePlaceholder')} /></Form.Item>
          <Form.Item name="report_type" label={t('reports.type')} rules={[{ required: true }]} initialValue="full">
            <Select>
              <Option value="quick">{t('reports.quick')}</Option>
              <Option value="full">{t('reports.full')}</Option>
              <Option value="comparison">{t('reports.comparison')}</Option>
            </Select>
          </Form.Item>
          <Form.Item name="target_type" label={t('reports.targetType')} rules={[{ required: true }]} initialValue="keyword">
            <Select>
              <Option value="keyword">{t('trends.keyword')}</Option>
              <Option value="category">{t('products.category')}</Option>
              <Option value="product">{t('products.product')}</Option>
            </Select>
          </Form.Item>
          <Form.Item name="target_value" label={t('reports.targetKeyword')} rules={[{ required: true }]}>
            <Input placeholder={t('reports.targetKeywordPlaceholder')} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={generating} block>{t('reports.generate')}</Button>
          </Form.Item>
        </Form>
      </Modal>

      {/* View Report Modal */}
      <Modal title={t('reports.view')} open={!!viewReport} onCancel={() => setViewReport(null)} width={900} footer={[
        <Button key="close" onClick={() => setViewReport(null)}>{t('products.close')}</Button>,
        <Button key="download" type="primary" icon={<DownloadOutlined />}>{t('reports.download')} PDF</Button>,
      ]}>
        {viewReport && (
          <>
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={8}>
                <Card><ReactECharts option={getScoreChartOption(viewReport)} style={{ height: 200 }} /></Card>
              </Col>
              <Col span={16}>
                <Card title="Summary">
                  <p><strong>Conclusion:</strong> {viewReport.summary?.conclusion || 'N/A'}</p>
                  <p><strong>Recommendation:</strong> <Tag color={viewReport.summary?.recommendation === 'recommended' ? 'green' : viewReport.summary?.recommendation === 'wait' ? 'orange' : 'red'}>{viewReport.summary?.recommendation || 'N/A'}</Tag></p>
                  {viewReport.summary?.key_points && (
                    <ul>{viewReport.summary.key_points.map((p, i) => <li key={i}>{p}</li>)}</ul>
                  )}
                </Card>
              </Col>
            </Row>
            <Descriptions bordered column={2}>
              <Descriptions.Item label={t('reports.type')}>{viewReport.report_type}</Descriptions.Item>
              <Descriptions.Item label={t('reports.status')}><Tag color="green">{viewReport.status}</Tag></Descriptions.Item>
              <Descriptions.Item label="Target">{viewReport.target_type}: {viewReport.target_value}</Descriptions.Item>
              <Descriptions.Item label={t('reports.score')}>{viewReport.overall_score}/100</Descriptions.Item>
              <Descriptions.Item label={t('reports.created')}>{new Date(viewReport.created_at).toLocaleString()}</Descriptions.Item>
              <Descriptions.Item label="Updated">{new Date(viewReport.updated_at).toLocaleString()}</Descriptions.Item>
            </Descriptions>
          </>
        )}
      </Modal>
    </div>
  );
};

export default Reports;
