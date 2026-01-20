import { useState, useEffect } from 'react';
import { Card, Button, Table, Tag, Space, Modal, Form, Input, Select, Progress, message, Descriptions, Row, Col, Statistic } from 'antd';
import { PlusOutlined, ReloadOutlined, DownloadOutlined, ShareAltOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { reportsApi } from '../services/api';
import type { Report, ReportCreate } from '../types';

const { Option } = Select;

const Reports = () => {
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
    } catch (error) { message.error('Failed to load reports'); }
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
      message.success('Report generation started!');
      setCreateModalOpen(false);
      form.resetFields();
      setTimeout(loadReports, 2000);
    } catch (error) { message.error('Failed to start report generation'); }
    finally { setGenerating(false); }
  };

  const handleDelete = async (id: string) => {
    try {
      await reportsApi.delete(id);
      message.success('Report deleted');
      loadReports();
    } catch (error) { message.error('Failed to delete report'); }
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
    { title: 'Title', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: 'Type', dataIndex: 'report_type', key: 'type', render: (t: string) => <Tag>{t.toUpperCase()}</Tag> },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string, r: Report) => (
      <Space>
        <Tag color={s === 'completed' ? 'green' : s === 'generating' ? 'blue' : s === 'failed' ? 'red' : 'default'}>{s}</Tag>
        {s === 'generating' && <Progress percent={r.progress} size="small" style={{ width: 100 }} />}
      </Space>
    )},
    { title: 'Score', dataIndex: 'overall_score', key: 'score', render: (s: number) => s ? <Tag color={s >= 70 ? 'green' : s >= 40 ? 'orange' : 'red'}>{s}/100</Tag> : '-' },
    { title: 'Created', dataIndex: 'created_at', key: 'created', render: (d: string) => new Date(d).toLocaleDateString() },
    { title: 'Actions', key: 'actions', render: (_: any, record: Report) => (
      <Space>
        <Button size="small" icon={<EyeOutlined />} onClick={() => setViewReport(record)} disabled={record.status !== 'completed'} />
        <Button size="small" icon={<DownloadOutlined />} disabled={!record.pdf_path} />
        <Button size="small" icon={<ShareAltOutlined />} disabled={record.status !== 'completed'} />
        <Button size="small" icon={<DeleteOutlined />} danger onClick={() => handleDelete(record.id)} />
      </Space>
    )},
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>Reports</h1>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadReports} loading={loading}>Refresh</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>New Report</Button>
        </Space>
      </div>

      <Card>
        <Table dataSource={reports} columns={columns} rowKey="id" loading={loading} pagination={{ pageSize: 10 }} />
      </Card>

      {/* Create Report Modal */}
      <Modal title="Generate New Report" open={createModalOpen} onCancel={() => setCreateModalOpen(false)} footer={null} width={500}>
        <Form form={form} layout="vertical" onFinish={handleCreateReport}>
          <Form.Item name="title" label="Report Title"><Input placeholder="Enter report title" /></Form.Item>
          <Form.Item name="report_type" label="Report Type" rules={[{ required: true }]} initialValue="full">
            <Select>
              <Option value="quick">Quick Report</Option>
              <Option value="full">Full Report</Option>
              <Option value="comparison">Comparison Report</Option>
            </Select>
          </Form.Item>
          <Form.Item name="target_type" label="Target Type" rules={[{ required: true }]} initialValue="keyword">
            <Select>
              <Option value="keyword">Keyword</Option>
              <Option value="category">Category</Option>
              <Option value="product">Product ID</Option>
            </Select>
          </Form.Item>
          <Form.Item name="target_value" label="Target Value" rules={[{ required: true }]}>
            <Input placeholder="Enter keyword, category, or product ID" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={generating} block>Generate Report</Button>
          </Form.Item>
        </Form>
      </Modal>

      {/* View Report Modal */}
      <Modal title="Report Details" open={!!viewReport} onCancel={() => setViewReport(null)} width={900} footer={[
        <Button key="close" onClick={() => setViewReport(null)}>Close</Button>,
        <Button key="download" type="primary" icon={<DownloadOutlined />}>Download PDF</Button>,
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
              <Descriptions.Item label="Report Type">{viewReport.report_type}</Descriptions.Item>
              <Descriptions.Item label="Status"><Tag color="green">{viewReport.status}</Tag></Descriptions.Item>
              <Descriptions.Item label="Target">{viewReport.target_type}: {viewReport.target_value}</Descriptions.Item>
              <Descriptions.Item label="Overall Score">{viewReport.overall_score}/100</Descriptions.Item>
              <Descriptions.Item label="Created">{new Date(viewReport.created_at).toLocaleString()}</Descriptions.Item>
              <Descriptions.Item label="Updated">{new Date(viewReport.updated_at).toLocaleString()}</Descriptions.Item>
            </Descriptions>
          </>
        )}
      </Modal>
    </div>
  );
};

export default Reports;
